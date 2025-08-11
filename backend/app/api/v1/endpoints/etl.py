from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.models import DataChangeLog, Project, Municipality
from app.db.session import get_db_session
from app.realtime.notifier import DataChangeNotifier
from app.services.change_detection import calculate_content_hash, diff_dicts
from app.services.etl_manager import ETLManager, trigger_dws_sync, trigger_treasury_sync, trigger_correlation_analysis, trigger_full_sync
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Pydantic models
class ETLTriggerRequest(BaseModel):
    source: str = 'all'  # 'all', 'dws', 'treasury', 'correlation'
    priority: Optional[int] = 5
    parameters: Optional[Dict[str, Any]] = None

class ETLJobResponse(BaseModel):
    job_id: str
    job_type: str
    source: str
    status: str
    message: str

class ETLStatusResponse(BaseModel):
    running: bool
    metrics: Dict[str, Any]
    active_jobs: List[Dict[str, Any]]
    data_sources_health: Dict[str, Any]


router = APIRouter()

# Global ETL Manager instance
_etl_manager: Optional[ETLManager] = None

def get_etl_manager() -> ETLManager:
    """Dependency to get ETL manager instance"""
    if _etl_manager is None:
        raise HTTPException(500, detail="ETL manager not initialized")
    return _etl_manager


@router.post("/trigger")
async def trigger_ingest(background: BackgroundTasks, session: AsyncSession = Depends(get_db_session)) -> dict:
    """Development-only ETL trigger: updates the demo project's progress to simulate change events."""
    result = await session.execute(select(Project).limit(1))
    project = result.scalar_one_or_none()
    if not project:
        return {"status": "no_project"}

    old = {
        "name": project.name,
        "status": project.status,
        "progress_percentage": project.progress_percentage,
    }
    # simulate a change
    new_progress = min(100, (project.progress_percentage or 0) + 5)
    project.progress_percentage = new_progress
    project.updated_at = datetime.utcnow()
    await session.commit()

    new = {
        "name": project.name,
        "status": project.status,
        "progress_percentage": project.progress_percentage,
    }
    changes, old_values = diff_dicts(old, new)

    # log change
    log = DataChangeLog(
        id=str(uuid.uuid4()),
        entity_type="project",
        entity_id=project.id,
        change_type="updated",
        field_changes=changes,
        old_values=old_values,
        new_values=changes,
        source="etl_pipeline",
        created_at=datetime.utcnow(),
    )
    session.add(log)
    await session.commit()

    # notify via websocket: use BackgroundTasks with app state notifier
    from fastapi import Request  # type: ignore
    # We'll attach a small closure run at response send-time using background tasks
    async def _notify():
        from app.main import app as fastapi_app  # global app
        notifier = fastapi_app.state.notifier
        await notifier.notify_change(
            {
                "entity_type": "project",
                "entity_id": project.id,
                "change_type": "updated",
                "changes": changes,
                "timestamp": datetime.utcnow(),
            }
        )

    background.add_task(_notify)
    return {"status": "ok", "project_id": project.id, "changes": changes}


@router.post("/dws-sync")
async def trigger_dws_sync(background: BackgroundTasks) -> dict:
    """Trigger a manual sync with the DWS Project Monitoring Dashboard."""
    
    async def _sync():
        from app.main import app as fastapi_app
        notifier = fastapi_app.state.notifier
        
        # Import here to avoid circular dependencies
        from app.etl.dws import EnhancedDWSMonitor
        
        dws_monitor = EnhancedDWSMonitor(notifier)
        try:
            await dws_monitor.poll_with_change_detection()
        except Exception as e:
            logger.error(f"DWS sync failed: {e}")
            await notifier.notify_system_error("DWS sync failed", str(e))
    
    background.add_task(_sync)
    return {"status": "ok", "message": "DWS sync triggered"}


@router.get("/status")
async def get_etl_status(session: AsyncSession = Depends(get_db_session)) -> dict:
    """Get ETL pipeline status and statistics."""
    
    # Get recent change logs
    recent_changes_stmt = select(DataChangeLog).order_by(DataChangeLog.created_at.desc()).limit(10)
    recent_changes_result = await session.execute(recent_changes_stmt)
    recent_changes = recent_changes_result.scalars().all()
    
    # Get simple counts
    total_projects_result = await session.execute(select(Project))
    total_projects = len(total_projects_result.scalars().all())
    
    total_municipalities_result = await session.execute(select(Municipality))
    total_municipalities = len(total_municipalities_result.scalars().all())
    
    return {
        "status": "active",
        "total_projects": total_projects,
        "total_municipalities": total_municipalities,
        "recent_changes": [
            {
                "id": change.id,
                "entity_type": change.entity_type,
                "entity_id": change.entity_id,
                "change_type": change.change_type,
                "source": change.source,
                "created_at": change.created_at.isoformat(),
                "field_changes": list(change.field_changes.keys()) if change.field_changes else []
            }
            for change in recent_changes
        ]
    }


# New ETL Manager Endpoints

@router.post("/manager/start")
async def start_etl_manager(etl_manager: ETLManager = Depends(get_etl_manager)) -> Dict[str, Any]:
    """Start the ETL manager"""
    try:
        await etl_manager.start()
        return {"status": "started", "message": "ETL Manager started successfully"}
    except Exception as e:
        logger.error(f"Failed to start ETL manager: {str(e)}")
        raise HTTPException(500, detail=f"Failed to start ETL manager: {str(e)}")


@router.post("/manager/stop")
async def stop_etl_manager(etl_manager: ETLManager = Depends(get_etl_manager)) -> Dict[str, Any]:
    """Stop the ETL manager"""
    try:
        await etl_manager.stop()
        return {"status": "stopped", "message": "ETL Manager stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop ETL manager: {str(e)}")
        raise HTTPException(500, detail=f"Failed to stop ETL manager: {str(e)}")


@router.get("/manager/status", response_model=ETLStatusResponse)
async def get_etl_manager_status(etl_manager: ETLManager = Depends(get_etl_manager)) -> ETLStatusResponse:
    """Get ETL manager status and metrics"""
    try:
        metrics = await etl_manager.get_metrics()
        active_jobs = await etl_manager.get_all_jobs(limit=50)
        
        return ETLStatusResponse(
            running=metrics['running'],
            metrics=metrics,
            active_jobs=active_jobs,
            data_sources_health=metrics['data_sources']
        )
    except Exception as e:
        logger.error(f"Failed to get ETL manager status: {str(e)}")
        raise HTTPException(500, detail=f"Failed to get ETL manager status: {str(e)}")


@router.post("/sync", response_model=ETLJobResponse)
async def trigger_etl_sync(
    request: ETLTriggerRequest,
    etl_manager: ETLManager = Depends(get_etl_manager)
) -> ETLJobResponse:
    """Trigger ETL synchronization with job management"""
    try:
        logger.info(f"Triggering ETL sync for source: {request.source}")
        
        # Validate source
        valid_sources = ['all', 'dws', 'treasury', 'correlation']
        if request.source not in valid_sources:
            raise HTTPException(400, detail=f"Invalid source. Must be one of: {valid_sources}")
        
        # Submit appropriate job(s)
        if request.source == 'all':
            job_ids = await trigger_full_sync(etl_manager, request.priority or 5)
            job_id = job_ids[0] if job_ids else "no-jobs-created"
            job_type = "full_sync"
        elif request.source == 'dws':
            job_id = await etl_manager.submit_job('dws_sync', 'dws', priority=request.priority or 5)
            job_type = "dws_sync"
        elif request.source == 'treasury':
            job_id = await etl_manager.submit_job('treasury_sync', 'treasury', priority=request.priority or 5)
            job_type = "treasury_sync"
        elif request.source == 'correlation':
            job_id = await etl_manager.submit_job('correlation_analysis', 'correlation', priority=request.priority or 5)
            job_type = "correlation_analysis"
        else:
            raise HTTPException(400, detail="Unsupported source")
        
        logger.info(f"ETL sync triggered: {job_id} ({job_type})")
        
        return ETLJobResponse(
            job_id=job_id,
            job_type=job_type,
            source=request.source,
            status="submitted",
            message=f"ETL sync job submitted for {request.source}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger ETL sync: {str(e)}")
        raise HTTPException(500, detail=f"Failed to trigger ETL sync: {str(e)}")


@router.get("/jobs")
async def get_etl_jobs(
    limit: int = 50,
    etl_manager: ETLManager = Depends(get_etl_manager)
) -> Dict[str, Any]:
    """Get list of ETL jobs"""
    try:
        jobs = await etl_manager.get_all_jobs(limit=limit)
        return {
            "jobs": jobs,
            "total": len(jobs),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get ETL jobs: {str(e)}")
        raise HTTPException(500, detail=f"Failed to get ETL jobs: {str(e)}")


@router.get("/jobs/{job_id}")
async def get_etl_job_status(
    job_id: str,
    etl_manager: ETLManager = Depends(get_etl_manager)
) -> Dict[str, Any]:
    """Get status of a specific ETL job"""
    try:
        job_status = await etl_manager.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(404, detail=f"Job {job_id} not found")
        
        return job_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(500, detail=f"Failed to get job status: {str(e)}")


@router.post("/jobs/{job_id}/cancel")
async def cancel_etl_job(
    job_id: str,
    etl_manager: ETLManager = Depends(get_etl_manager)
) -> Dict[str, Any]:
    """Cancel a specific ETL job"""
    try:
        success = await etl_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(404, detail=f"Job {job_id} not found or cannot be cancelled")
        
        return {"status": "cancelled", "job_id": job_id, "message": "Job cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}")
        raise HTTPException(500, detail=f"Failed to cancel job: {str(e)}")


@router.post("/jobs/{job_id}/retry")
async def retry_etl_job(
    job_id: str,
    etl_manager: ETLManager = Depends(get_etl_manager)
) -> Dict[str, Any]:
    """Retry a failed ETL job"""
    try:
        success = await etl_manager.retry_job(job_id)
        if not success:
            raise HTTPException(404, detail=f"Job {job_id} not found or cannot be retried")
        
        return {"status": "retried", "job_id": job_id, "message": "Job retry submitted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job: {str(e)}")
        raise HTTPException(500, detail=f"Failed to retry job: {str(e)}")


# Utility function for initialization (called during app startup)

def initialize_etl_manager(notification_manager: DataChangeNotifier) -> None:
    """Initialize global ETL manager instance"""
    global _etl_manager
    _etl_manager = ETLManager(notification_manager)
    logger.info("ETL Manager initialized")

