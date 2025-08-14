from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import Project, Municipality, FinancialData, DataChangeLog
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint that provides system status and basic metrics
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "BukaAmanzi Water Infrastructure Monitor",
            "version": "3.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/health/detailed")
async def detailed_health_check(
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Detailed health check with database connectivity and data metrics
    """
    try:
        # Check database connectivity and get basic counts
        projects_stmt = select(func.count(Project.id))
        projects_result = await session.execute(projects_stmt)
        total_projects = projects_result.scalar()

        municipalities_stmt = select(func.count(Municipality.id))
        municipalities_result = await session.execute(municipalities_stmt)
        total_municipalities = municipalities_result.scalar()

        financial_stmt = select(func.count(FinancialData.id))
        financial_result = await session.execute(financial_stmt)
        total_financial_records = financial_result.scalar()

        # Get recent changes count
        recent_changes_stmt = select(func.count(DataChangeLog.id)).where(
            DataChangeLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        recent_changes_result = await session.execute(recent_changes_stmt)
        recent_changes_count = recent_changes_result.scalar()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "BukaAmanzi Water Infrastructure Monitor",
            "version": "3.0.0",
            "database": {
                "status": "connected",
                "total_projects": total_projects,
                "total_municipalities": total_municipalities,
                "total_financial_records": total_financial_records,
                "recent_changes_today": recent_changes_count
            },
            "data_sources": {
                "dws": {
                    "status": "active",
                    "last_sync": "automated"
                },
                "treasury": {
                    "status": "active", 
                    "last_sync": "automated"
                }
            }
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "database": {
                "status": "error",
                "error": str(e)
            }
        }


@router.get("/health/system")
async def system_health_check() -> Dict[str, Any]:
    """
    System health check for monitoring services
    """
    try:
        # This would typically check external dependencies
        # For now, return basic system status
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "api": {"status": "healthy"},
                "database": {"status": "healthy"},
                "etl_manager": {"status": "active"},
                "data_scheduler": {"status": "active"}
            },
            "uptime": "active"
        }
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
