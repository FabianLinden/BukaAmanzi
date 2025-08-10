from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DataChangeLog, Project, Municipality
from app.db.session import get_db_session
from app.realtime.notifier import DataChangeNotifier
from app.services.change_detection import calculate_content_hash, diff_dicts
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


router = APIRouter()


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

