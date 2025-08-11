from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from uuid import uuid4

from app.etl.dws import EnhancedDWSMonitor
from app.etl.treasury import MunicipalTreasuryETL
from app.services.data_correlation import DataCorrelationService
from app.services.data_scheduler import DataScheduler
from app.services.change_detection import calculate_content_hash
from app.realtime.notifier import DataChangeNotifier
from app.db.session import async_session_factory
from app.db.models import DataChangeLog, Municipality, Project, FinancialData
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ETLJobStatus:
    """ETL Job status tracking"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ETLJob:
    """Represents an ETL job with tracking and result storage"""
    
    def __init__(
        self,
        job_id: str,
        job_type: str,
        source: str,
        parameters: Dict[str, Any] = None,
        priority: int = 5
    ):
        self.job_id = job_id
        self.job_type = job_type  # 'dws_sync', 'treasury_sync', 'correlation_analysis'
        self.source = source
        self.parameters = parameters or {}
        self.priority = priority
        self.status = ETLJobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.progress_percentage: int = 0
        self.retry_count: int = 0
        self.max_retries: int = 3


class ETLManager:
    """Comprehensive ETL Management Service"""
    
    def __init__(self, notification_manager: DataChangeNotifier):
        self.notification_manager = notification_manager
        self.dws_monitor = EnhancedDWSMonitor(notification_manager)
        self.correlation_service = DataCorrelationService(notification_manager)
        self.data_scheduler = DataScheduler(notification_manager)
        
        # Job queue and processing
        self.job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_jobs: Dict[str, ETLJob] = {}
        self.completed_jobs: Dict[str, ETLJob] = {}
        self.job_history_limit = 1000
        
        # Worker management
        self.max_concurrent_jobs = 3
        self.worker_tasks: List[asyncio.Task] = []
        self.running = False
        
        # Health and performance tracking
        self.metrics = {
            'total_jobs_processed': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'average_processing_time': 0.0,
            'last_activity': None,
            'data_sources_status': {
                'dws': {'status': 'unknown', 'last_sync': None, 'error_count': 0},
                'treasury': {'status': 'unknown', 'last_sync': None, 'error_count': 0},
                'correlation': {'status': 'unknown', 'last_sync': None, 'error_count': 0}
            }
        }
        
        # Configuration
        self.config = {
            'job_timeout': 3600,  # 1 hour
            'retry_delay': 300,   # 5 minutes
            'health_check_interval': 300,  # 5 minutes
            'cleanup_interval': 86400,  # 24 hours
            'max_job_history': 1000,
        }
        
    async def start(self) -> None:
        """Start the ETL manager and worker tasks"""
        if self.running:
            logger.warning("ETL Manager is already running")
            return
            
        logger.info("Starting ETL Manager...")
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_jobs):
            task = asyncio.create_task(self._worker_loop(f"worker-{i+1}"))
            self.worker_tasks.append(task)
            
        # Start health monitoring task
        health_task = asyncio.create_task(self._health_monitor_loop())
        self.worker_tasks.append(health_task)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.worker_tasks.append(cleanup_task)
        
        logger.info(f"ETL Manager started with {len(self.worker_tasks)} background tasks")
        
        # Notify startup
        await self.notification_manager.notify_system_event(
            "etl_manager_started",
            {"timestamp": datetime.utcnow().isoformat(), "workers": len(self.worker_tasks)}
        )
        
    async def stop(self) -> None:
        """Stop the ETL manager and all worker tasks"""
        if not self.running:
            return
            
        logger.info("Stopping ETL Manager...")
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        # Cancel active jobs
        for job in self.active_jobs.values():
            job.status = ETLJobStatus.CANCELLED
            
        logger.info("ETL Manager stopped")
        
        # Notify shutdown
        await self.notification_manager.notify_system_event(
            "etl_manager_stopped",
            {"timestamp": datetime.utcnow().isoformat()}
        )
        
    async def submit_job(
        self,
        job_type: str,
        source: str,
        parameters: Dict[str, Any] = None,
        priority: int = 5
    ) -> str:
        """Submit a new ETL job for processing"""
        job_id = str(uuid4())
        job = ETLJob(job_id, job_type, source, parameters, priority)
        
        # Add to queue with priority (lower number = higher priority)
        await self.job_queue.put((priority, job))
        
        logger.info(f"Submitted ETL job: {job_id} ({job_type}, {source})")
        
        # Notify job submission
        await self.notification_manager.notify_change({
            'entity_type': 'etl_job',
            'entity_id': job_id,
            'change_type': 'submitted',
            'changes': {'job_type': job_type, 'source': source},
            'timestamp': datetime.utcnow(),
        })
        
        return job_id
        
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        # Check active jobs first
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
        elif job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
        else:
            return None
            
        return {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'source': job.source,
            'status': job.status,
            'progress_percentage': job.progress_percentage,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message,
            'result': job.result,
            'retry_count': job.retry_count,
            'max_retries': job.max_retries
        }
        
    async def get_all_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get status of all recent jobs"""
        all_jobs = []
        
        # Add active jobs
        for job in self.active_jobs.values():
            all_jobs.append(await self.get_job_status(job.job_id))
            
        # Add completed jobs (most recent first)
        completed_jobs_list = list(self.completed_jobs.values())
        completed_jobs_list.sort(key=lambda x: x.completed_at or x.created_at, reverse=True)
        
        for job in completed_jobs_list[:limit-len(all_jobs)]:
            all_jobs.append(await self.get_job_status(job.job_id))
            
        return all_jobs
        
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = ETLJobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            
            # Move to completed jobs
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]
            
            logger.info(f"Cancelled ETL job: {job_id}")
            
            await self.notification_manager.notify_change({
                'entity_type': 'etl_job',
                'entity_id': job_id,
                'change_type': 'cancelled',
                'changes': {'status': 'cancelled'},
                'timestamp': datetime.utcnow(),
            })
            
            return True
            
        return False
        
    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job"""
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            if job.status == ETLJobStatus.FAILED and job.retry_count < job.max_retries:
                # Reset job status and resubmit
                job.status = ETLJobStatus.PENDING
                job.retry_count += 1
                job.started_at = None
                job.completed_at = None
                job.error_message = None
                job.progress_percentage = 0
                
                # Resubmit to queue
                await self.job_queue.put((job.priority, job))
                
                # Remove from completed jobs
                del self.completed_jobs[job_id]
                
                logger.info(f"Retrying ETL job: {job_id} (attempt {job.retry_count})")
                
                await self.notification_manager.notify_change({
                    'entity_type': 'etl_job',
                    'entity_id': job_id,
                    'change_type': 'retried',
                    'changes': {'retry_count': job.retry_count},
                    'timestamp': datetime.utcnow(),
                })
                
                return True
                
        return False
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get ETL processing metrics and health status"""
        current_time = datetime.utcnow()
        
        # Calculate queue size
        queue_size = self.job_queue.qsize()
        
        # Calculate uptime if running
        uptime_seconds = 0
        if self.running and self.metrics.get('start_time'):
            uptime_seconds = (current_time - self.metrics['start_time']).total_seconds()
            
        metrics = {
            'running': self.running,
            'current_time': current_time.isoformat(),
            'queue_size': queue_size,
            'active_jobs_count': len(self.active_jobs),
            'completed_jobs_count': len(self.completed_jobs),
            'uptime_seconds': uptime_seconds,
            'performance': {
                'total_jobs_processed': self.metrics['total_jobs_processed'],
                'successful_jobs': self.metrics['successful_jobs'],
                'failed_jobs': self.metrics['failed_jobs'],
                'success_rate': (self.metrics['successful_jobs'] / max(1, self.metrics['total_jobs_processed'])) * 100,
                'average_processing_time': self.metrics['average_processing_time']
            },
            'data_sources': self.metrics['data_sources_status'],
            'worker_status': {
                'max_concurrent_jobs': self.max_concurrent_jobs,
                'active_workers': len([t for t in self.worker_tasks if not t.done()]),
                'total_worker_tasks': len(self.worker_tasks)
            }
        }
        
        return metrics
        
    async def _worker_loop(self, worker_name: str) -> None:
        """Main worker loop for processing ETL jobs"""
        logger.info(f"Starting ETL worker: {worker_name}")
        
        while self.running:
            try:
                # Wait for a job with timeout
                try:
                    priority, job = await asyncio.wait_for(
                        self.job_queue.get(), timeout=10
                    )
                except asyncio.TimeoutError:
                    continue
                    
                # Process the job
                await self._process_job(job, worker_name)
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} encountered error: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error
                
        logger.info(f"ETL worker {worker_name} stopped")
        
    async def _process_job(self, job: ETLJob, worker_name: str) -> None:
        """Process a single ETL job"""
        logger.info(f"Worker {worker_name} processing job {job.job_id} ({job.job_type})")
        
        # Move to active jobs
        self.active_jobs[job.job_id] = job
        
        # Update job status
        job.status = ETLJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.progress_percentage = 0
        
        try:
            # Execute job based on type
            if job.job_type == 'dws_sync':
                result = await self._execute_dws_sync(job)
            elif job.job_type == 'treasury_sync':
                result = await self._execute_treasury_sync(job)
            elif job.job_type == 'correlation_analysis':
                result = await self._execute_correlation_analysis(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
                
            # Job completed successfully
            job.status = ETLJobStatus.SUCCESS
            job.result = result
            job.progress_percentage = 100
            self.metrics['successful_jobs'] += 1
            
            # Update data source status
            self.metrics['data_sources_status'][job.source] = {
                'status': 'healthy',
                'last_sync': datetime.utcnow().isoformat(),
                'error_count': 0
            }
            
            logger.info(f"Job {job.job_id} completed successfully by {worker_name}")
            
        except Exception as e:
            # Job failed
            job.status = ETLJobStatus.FAILED
            job.error_message = str(e)
            self.metrics['failed_jobs'] += 1
            
            # Update data source status
            source_status = self.metrics['data_sources_status'][job.source]
            source_status['status'] = 'error'
            source_status['error_count'] = source_status.get('error_count', 0) + 1
            
            logger.error(f"Job {job.job_id} failed in {worker_name}: {str(e)}")
            
            # Notify job failure
            await self.notification_manager.notify_system_error(
                f"ETL Job Failed: {job.job_type}",
                str(e),
                {'job_id': job.job_id, 'worker': worker_name}
            )
            
        finally:
            # Complete job processing
            job.completed_at = datetime.utcnow()
            
            # Calculate processing time
            if job.started_at:
                processing_time = (job.completed_at - job.started_at).total_seconds()
                
                # Update average processing time
                total_jobs = self.metrics['total_jobs_processed']
                current_avg = self.metrics['average_processing_time']
                self.metrics['average_processing_time'] = (
                    (current_avg * total_jobs + processing_time) / (total_jobs + 1)
                )
                
            self.metrics['total_jobs_processed'] += 1
            self.metrics['last_activity'] = datetime.utcnow().isoformat()
            
            # Move to completed jobs
            self.completed_jobs[job.job_id] = job
            del self.active_jobs[job.job_id]
            
            # Notify job completion
            await self.notification_manager.notify_change({
                'entity_type': 'etl_job',
                'entity_id': job.job_id,
                'change_type': 'completed',
                'changes': {
                    'status': job.status,
                    'processing_time_seconds': processing_time if job.started_at else 0
                },
                'timestamp': datetime.utcnow(),
            })
            
    async def _execute_dws_sync(self, job: ETLJob) -> Dict[str, Any]:
        """Execute DWS data synchronization"""
        job.progress_percentage = 10
        
        # Poll DWS data with change detection
        await self.dws_monitor.poll_with_change_detection()
        job.progress_percentage = 100
        
        return {
            'source': 'dws',
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def _execute_treasury_sync(self, job: ETLJob) -> Dict[str, Any]:
        """Execute Treasury data synchronization"""
        job.progress_percentage = 10
        
        # Use Treasury ETL with async context manager
        async with MunicipalTreasuryETL(self.notification_manager) as treasury_etl:
            job.progress_percentage = 30
            await treasury_etl.poll_with_change_detection()
            job.progress_percentage = 100
        
        return {
            'source': 'treasury',
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def _execute_correlation_analysis(self, job: ETLJob) -> Dict[str, Any]:
        """Execute correlation analysis"""
        job.progress_percentage = 10
        
        # Run correlation analysis for all projects
        correlation_results = await self.correlation_service.correlate_all_projects()
        job.progress_percentage = 100
        
        return {
            'source': 'correlation',
            'status': 'completed',
            'results': correlation_results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def _health_monitor_loop(self) -> None:
        """Monitor health of ETL processes"""
        while self.running:
            try:
                await self._update_health_metrics()
                await asyncio.sleep(self.config['health_check_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {str(e)}")
                await asyncio.sleep(30)
                
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of old jobs and logs"""
        while self.running:
            try:
                await asyncio.sleep(self.config['cleanup_interval'])
                if not self.running:
                    break
                    
                # Cleanup old completed jobs
                current_time = datetime.utcnow()
                jobs_to_remove = []
                
                for job_id, job in self.completed_jobs.items():
                    if job.completed_at:
                        age = (current_time - job.completed_at).total_seconds()
                        if age > 86400:  # Remove jobs older than 24 hours
                            jobs_to_remove.append(job_id)
                            
                for job_id in jobs_to_remove:
                    del self.completed_jobs[job_id]
                    
                if jobs_to_remove:
                    logger.info(f"Cleaned up {len(jobs_to_remove)} old completed jobs")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                
    async def _update_health_metrics(self) -> None:
        """Update health and performance metrics"""
        try:
            # Update worker health
            active_workers = len([t for t in self.worker_tasks if not t.done()])
            if active_workers < self.max_concurrent_jobs:
                logger.warning(f"Only {active_workers}/{self.max_concurrent_jobs} workers active")
                
            # Check for stuck jobs
            current_time = datetime.utcnow()
            stuck_jobs = []
            
            for job in self.active_jobs.values():
                if job.started_at:
                    processing_time = (current_time - job.started_at).total_seconds()
                    if processing_time > self.config['job_timeout']:
                        stuck_jobs.append(job.job_id)
                        
            if stuck_jobs:
                logger.warning(f"Detected {len(stuck_jobs)} potentially stuck jobs")
                for job_id in stuck_jobs:
                    await self.cancel_job(job_id)
                    
        except Exception as e:
            logger.error(f"Error updating health metrics: {str(e)}")


# Convenience functions for triggering ETL processes

async def trigger_dws_sync(etl_manager: ETLManager, priority: int = 5) -> str:
    """Trigger DWS data synchronization"""
    return await etl_manager.submit_job('dws_sync', 'dws', priority=priority)

async def trigger_treasury_sync(etl_manager: ETLManager, priority: int = 5) -> str:
    """Trigger Treasury data synchronization"""  
    return await etl_manager.submit_job('treasury_sync', 'treasury', priority=priority)

async def trigger_correlation_analysis(etl_manager: ETLManager, priority: int = 5) -> str:
    """Trigger correlation analysis"""
    return await etl_manager.submit_job('correlation_analysis', 'correlation', priority=priority)

async def trigger_full_sync(etl_manager: ETLManager, priority: int = 5) -> List[str]:
    """Trigger full synchronization of all data sources"""
    job_ids = []
    
    # Submit jobs in order of dependency
    job_ids.append(await trigger_dws_sync(etl_manager, priority))
    job_ids.append(await trigger_treasury_sync(etl_manager, priority))
    job_ids.append(await trigger_correlation_analysis(etl_manager, priority + 1))  # Run after data sync
    
    return job_ids
