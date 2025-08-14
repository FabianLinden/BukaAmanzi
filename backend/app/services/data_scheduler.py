from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from uuid import uuid4

from app.etl.dws import EnhancedDWSMonitor
from app.etl.treasury import MunicipalTreasuryETL
from app.services.data_correlation import DataCorrelationService
from app.realtime.notifier import DataChangeNotifier
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataScheduler:
    """Coordinated scheduler for automated data polling and correlation"""
    
    def __init__(self, notification_manager: DataChangeNotifier):
        self.notification_manager = notification_manager
        self.dws_monitor = EnhancedDWSMonitor(notification_manager)
        self.treasury_etl = MunicipalTreasuryETL(notification_manager)
        self.correlation_service = DataCorrelationService(notification_manager)
        
        # Scheduling configuration
        self.config = {
            'dws_polling_interval': 1800,  # 30 minutes
            'treasury_polling_interval': 3600,  # 1 hour
            'correlation_interval': 7200,  # 2 hours
            'health_check_interval': 300,  # 5 minutes
            'retry_attempts': 3,
            'retry_delay': 300,  # 5 minutes
            'rate_limit_delay': 2.0,  # seconds between operations
        }
        
        # Scheduler state
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}
        self.last_run_times: Dict[str, datetime] = {}
        self.error_counts: Dict[str, int] = {}
        self.health_status: Dict[str, Any] = {
            'dws_status': 'stopped',
            'treasury_status': 'stopped',
            'correlation_status': 'stopped',
            'last_successful_sync': None,
            'total_errors': 0,
            'uptime_start': None
        }
    
    async def start_scheduler(self) -> None:
        """Start all automated polling tasks"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting Data Scheduler...")
        self.running = True
        self.health_status['uptime_start'] = datetime.utcnow()
        
        # Start individual polling tasks
        try:
            # Health monitoring task
            self.tasks['health_monitor'] = asyncio.create_task(
                self._health_monitor_loop()
            )
            
            # DWS polling task
            self.tasks['dws_polling'] = asyncio.create_task(
                self._dws_polling_loop()
            )
            
            # Treasury polling task  
            self.tasks['treasury_polling'] = asyncio.create_task(
                self._treasury_polling_loop()
            )
            
            # Correlation analysis task
            self.tasks['correlation_analysis'] = asyncio.create_task(
                self._correlation_analysis_loop()
            )
            
            # Periodic maintenance task
            self.tasks['maintenance'] = asyncio.create_task(
                self._maintenance_loop()
            )
            
            logger.info(f"Started {len(self.tasks)} scheduler tasks")

            # Notify that scheduler has started (with error handling for Redis issues)
            try:
                await self.notification_manager.notify_system_event(
                    "scheduler_started",
                    {"timestamp": datetime.utcnow().isoformat(), "tasks": list(self.tasks.keys())}
                )
            except Exception as e:
                logger.warning(f"Could not send scheduler startup notification (Redis unavailable): {e}")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            await self.stop_scheduler()
            raise
    
    async def stop_scheduler(self) -> None:
        """Stop all polling tasks"""
        if not self.running:
            return
        
        logger.info("Stopping Data Scheduler...")
        self.running = False
        
        # Cancel all running tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                logger.info(f"Cancelling task: {task_name}")
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task {task_name} cancelled successfully")
                except Exception as e:
                    logger.error(f"Error cancelling task {task_name}: {str(e)}")
        
        self.tasks.clear()
        
        # Update health status
        for key in self.health_status:
            if key.endswith('_status'):
                self.health_status[key] = 'stopped'
        
        logger.info("Data Scheduler stopped")
        
        # Notify that scheduler has stopped
        await self.notification_manager.notify_system_event(
            "scheduler_stopped",
            {"timestamp": datetime.utcnow().isoformat()}
        )
    
    async def _health_monitor_loop(self) -> None:
        """Monitor health of all scheduler components"""
        while self.running:
            try:
                await self._update_health_status()
                await asyncio.sleep(self.config['health_check_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {str(e)}")
                await asyncio.sleep(30)  # Brief pause on error
    
    async def _dws_polling_loop(self) -> None:
        """Main DWS data polling loop"""
        while self.running:
            try:
                self.health_status['dws_status'] = 'running'
                logger.info("Starting DWS data polling cycle")
                
                # Poll DWS data with change detection
                await self.dws_monitor.poll_with_change_detection()
                
                self.last_run_times['dws'] = datetime.utcnow()
                self.error_counts['dws'] = 0  # Reset error count on success
                self.health_status['dws_status'] = 'healthy'
                self.health_status['last_successful_sync'] = datetime.utcnow()
                
                logger.info("DWS polling cycle completed successfully")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_counts['dws'] = self.error_counts.get('dws', 0) + 1
                self.health_status['dws_status'] = 'error'
                self.health_status['total_errors'] += 1
                
                logger.error(f"Error in DWS polling (attempt {self.error_counts['dws']}): {str(e)}")
                
                # Exponential backoff on repeated errors
                delay = min(300 * (2 ** (self.error_counts['dws'] - 1)), 3600)  # Max 1 hour
                await asyncio.sleep(delay)
                continue
            
            # Wait for next polling cycle
            await asyncio.sleep(self.config['dws_polling_interval'])
    
    async def _treasury_polling_loop(self) -> None:
        """Main Treasury data polling loop"""
        while self.running:
            try:
                self.health_status['treasury_status'] = 'running'
                logger.info("Starting Treasury data polling cycle")
                
                # Use Treasury ETL with async context manager
                async with self.treasury_etl:
                    await self.treasury_etl.poll_with_change_detection()
                
                self.last_run_times['treasury'] = datetime.utcnow()
                self.error_counts['treasury'] = 0  # Reset error count on success
                self.health_status['treasury_status'] = 'healthy'
                self.health_status['last_successful_sync'] = datetime.utcnow()
                
                logger.info("Treasury polling cycle completed successfully")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_counts['treasury'] = self.error_counts.get('treasury', 0) + 1
                self.health_status['treasury_status'] = 'error'
                self.health_status['total_errors'] += 1
                
                logger.error(f"Error in Treasury polling (attempt {self.error_counts['treasury']}): {str(e)}")
                
                # Exponential backoff on repeated errors
                delay = min(300 * (2 ** (self.error_counts['treasury'] - 1)), 3600)  # Max 1 hour
                await asyncio.sleep(delay)
                continue
            
            # Wait for next polling cycle
            await asyncio.sleep(self.config['treasury_polling_interval'])
    
    async def _correlation_analysis_loop(self) -> None:
        """Correlation analysis loop"""
        while self.running:
            try:
                self.health_status['correlation_status'] = 'running'
                logger.info("Starting correlation analysis cycle")
                
                # Run correlation analysis for all projects
                correlation_results = await self.correlation_service.correlate_all_projects()
                
                # Send correlation update notification
                await self.notification_manager.notify_change({
                    'entity_type': 'correlation_analysis',
                    'change_type': 'bulk_analysis',
                    'changes': {
                        'projects_analyzed': correlation_results['summary']['total_projects'],
                        'correlations_found': correlation_results['summary']['projects_with_financial_data'],
                        'high_risk_projects': correlation_results['summary']['high_risk_projects']
                    },
                    'timestamp': datetime.utcnow(),
                })
                
                self.last_run_times['correlation'] = datetime.utcnow()
                self.error_counts['correlation'] = 0
                self.health_status['correlation_status'] = 'healthy'
                
                logger.info(f"Correlation analysis completed - analyzed {correlation_results['summary']['total_projects']} projects")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_counts['correlation'] = self.error_counts.get('correlation', 0) + 1
                self.health_status['correlation_status'] = 'error'
                self.health_status['total_errors'] += 1
                
                logger.error(f"Error in correlation analysis: {str(e)}")
                await asyncio.sleep(300)  # 5 minute delay on error
                continue
            
            # Wait for next analysis cycle
            await asyncio.sleep(self.config['correlation_interval'])
    
    async def _maintenance_loop(self) -> None:
        """Periodic maintenance tasks"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                if not self.running:
                    break
                
                logger.info("Running scheduled maintenance tasks")
                
                # Clear old error counts
                current_time = datetime.utcnow()
                for task_name in list(self.error_counts.keys()):
                    if (current_time - self.last_run_times.get(task_name, current_time)).total_seconds() > 7200:  # 2 hours
                        self.error_counts[task_name] = 0
                
                # Check for stuck tasks and restart if needed
                await self._restart_failed_tasks()
                
                logger.info("Maintenance tasks completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {str(e)}")
                continue
    
    async def _restart_failed_tasks(self) -> None:
        """Restart tasks that have failed multiple times"""
        for task_name, error_count in self.error_counts.items():
            if error_count > self.config['retry_attempts']:
                logger.warning(f"Task {task_name} has failed {error_count} times, attempting restart")
                
                if task_name in self.tasks:
                    # Cancel the failed task
                    self.tasks[task_name].cancel()
                    try:
                        await self.tasks[task_name]
                    except asyncio.CancelledError:
                        pass
                    
                    # Restart the task
                    if task_name == 'dws_polling':
                        self.tasks[task_name] = asyncio.create_task(self._dws_polling_loop())
                    elif task_name == 'treasury_polling':
                        self.tasks[task_name] = asyncio.create_task(self._treasury_polling_loop())
                    elif task_name == 'correlation_analysis':
                        self.tasks[task_name] = asyncio.create_task(self._correlation_analysis_loop())
                    
                    # Reset error count
                    self.error_counts[task_name] = 0
                    
                    logger.info(f"Restarted task: {task_name}")
    
    async def _update_health_status(self) -> None:
        """Update overall health status"""
        try:
            current_time = datetime.utcnow()
            
            # Update uptime
            if self.health_status['uptime_start']:
                uptime = current_time - self.health_status['uptime_start']
                self.health_status['uptime_seconds'] = int(uptime.total_seconds())
            
            # Check task health
            for task_name, task in self.tasks.items():
                if task.done() and not task.cancelled():
                    self.health_status[f'{task_name}_status'] = 'failed'
            
            # Update last run times health
            for task_name in ['dws', 'treasury', 'correlation']:
                if task_name in self.last_run_times:
                    time_since_last = current_time - self.last_run_times[task_name]
                    expected_interval = self.config.get(f'{task_name}_polling_interval', 3600)
                    
                    if time_since_last.total_seconds() > expected_interval * 2:  # Double the expected interval
                        self.health_status[f'{task_name}_status'] = 'stale'
            
            # Send periodic health update
            if current_time.minute % 10 == 0:  # Every 10 minutes
                await self.notification_manager.notify_system_event(
                    "scheduler_health_update",
                    self.health_status.copy()
                )
            
        except Exception as e:
            logger.error(f"Error updating health status: {str(e)}")
    
    async def trigger_immediate_sync(self, source: str = 'all') -> Dict[str, Any]:
        """Trigger immediate data synchronization"""
        logger.info(f"Triggering immediate sync for: {source}")
        results = {}
        
        try:
            if source in ['all', 'dws']:
                logger.info("Running immediate DWS sync")
                await self.dws_monitor.poll_with_change_detection()
                results['dws'] = 'completed'
                
            if source in ['all', 'treasury']:
                logger.info("Running immediate Treasury sync")
                async with self.treasury_etl:
                    await self.treasury_etl.poll_with_change_detection()
                results['treasury'] = 'completed'
                
            if source in ['all', 'correlation']:
                logger.info("Running immediate correlation analysis")
                correlation_results = await self.correlation_service.correlate_all_projects()
                results['correlation'] = correlation_results['summary']
            
            results['trigger_time'] = datetime.utcnow().isoformat()
            results['status'] = 'success'
            
            # Notify about manual sync
            await self.notification_manager.notify_system_event(
                "manual_sync_triggered",
                {'source': source, 'results': results}
            )
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            logger.error(f"Error in immediate sync: {str(e)}")
            
        return results
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics"""
        current_time = datetime.utcnow()
        
        status = {
            'running': self.running,
            'health_status': self.health_status.copy(),
            'last_run_times': {
                k: v.isoformat() if v else None 
                for k, v in self.last_run_times.items()
            },
            'error_counts': self.error_counts.copy(),
            'config': self.config.copy(),
            'active_tasks': list(self.tasks.keys()),
            'current_time': current_time.isoformat()
        }
        
        # Add next scheduled run times
        status['next_runs'] = {}
        for task_name in ['dws', 'treasury', 'correlation']:
            if task_name in self.last_run_times:
                interval_key = f'{task_name}_polling_interval' if task_name != 'correlation' else 'correlation_interval'
                interval = self.config.get(interval_key, 3600)
                next_run = self.last_run_times[task_name] + timedelta(seconds=interval)
                status['next_runs'][task_name] = next_run.isoformat()
        
        return status
    
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update scheduler configuration"""
        logger.info(f"Updating scheduler configuration: {new_config}")
        
        # Validate configuration
        valid_keys = set(self.config.keys())
        invalid_keys = set(new_config.keys()) - valid_keys
        
        if invalid_keys:
            raise ValueError(f"Invalid configuration keys: {invalid_keys}")
        
        # Update configuration
        self.config.update(new_config)
        
        # Notify about configuration change
        await self.notification_manager.notify_system_event(
            "scheduler_config_updated",
            {'new_config': new_config, 'timestamp': datetime.utcnow().isoformat()}
        )
