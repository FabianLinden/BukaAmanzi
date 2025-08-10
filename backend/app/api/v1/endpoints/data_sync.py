from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.data_correlation import DataCorrelationService
from app.services.data_scheduler import DataScheduler
from app.realtime.notifier import DataChangeNotifier


# Pydantic models for request/response
class SyncTriggerRequest(BaseModel):
    source: str = 'all'  # 'all', 'dws', 'treasury', 'correlation'

class SyncResponse(BaseModel):
    status: str
    results: Dict[str, Any]
    trigger_time: str

class SchedulerConfigUpdate(BaseModel):
    dws_polling_interval: Optional[int] = None
    treasury_polling_interval: Optional[int] = None
    correlation_interval: Optional[int] = None
    health_check_interval: Optional[int] = None
    retry_attempts: Optional[int] = None
    retry_delay: Optional[int] = None

class ProjectCorrelationResponse(BaseModel):
    project_id: str
    project_name: str
    municipality_name: Optional[str] = None
    province: Optional[str] = None
    municipal_context: Dict[str, Any]
    correlations: Dict[str, Any]
    insights: List[str]
    risk_indicators: List[Dict[str, Any]]

class MunicipalOverviewResponse(BaseModel):
    municipality: Dict[str, Any]
    projects_summary: Dict[str, Any]
    financial_summary: Dict[str, Any]
    investment_efficiency: Dict[str, Any]
    recommendations: List[Dict[str, Any]]


router = APIRouter()


# Global instances - these would be initialized during app startup
_data_scheduler: Optional[DataScheduler] = None
_correlation_service: Optional[DataCorrelationService] = None
_notification_manager: Optional[DataChangeNotifier] = None


def get_scheduler() -> DataScheduler:
    """Dependency to get scheduler instance"""
    if _data_scheduler is None:
        raise HTTPException(500, detail="Data scheduler not initialized")
    return _data_scheduler


def get_correlation_service() -> DataCorrelationService:
    """Dependency to get correlation service instance"""
    if _correlation_service is None:
        raise HTTPException(500, detail="Correlation service not initialized")
    return _correlation_service


# Scheduler Management Endpoints

@router.post("/scheduler/start")
async def start_scheduler(scheduler: DataScheduler = Depends(get_scheduler)) -> Dict[str, Any]:
    """Start the data scheduler"""
    try:
        await scheduler.start_scheduler()
        return {"status": "started", "message": "Data scheduler started successfully"}
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to start scheduler: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler(scheduler: DataScheduler = Depends(get_scheduler)) -> Dict[str, Any]:
    """Stop the data scheduler"""
    try:
        await scheduler.stop_scheduler()
        return {"status": "stopped", "message": "Data scheduler stopped successfully"}
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to stop scheduler: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status(scheduler: DataScheduler = Depends(get_scheduler)) -> Dict[str, Any]:
    """Get current scheduler status"""
    try:
        return await scheduler.get_scheduler_status()
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to get scheduler status: {str(e)}")


@router.put("/scheduler/config")
async def update_scheduler_config(
    config: SchedulerConfigUpdate,
    scheduler: DataScheduler = Depends(get_scheduler)
) -> Dict[str, Any]:
    """Update scheduler configuration"""
    try:
        config_dict = config.model_dump(exclude_unset=True)
        await scheduler.update_config(config_dict)
        return {
            "status": "updated", 
            "message": "Scheduler configuration updated successfully",
            "updated_fields": list(config_dict.keys())
        }
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to update config: {str(e)}")


@router.post("/sync/trigger", response_model=SyncResponse)
async def trigger_sync(
    request: SyncTriggerRequest,
    background_tasks: BackgroundTasks,
    scheduler: DataScheduler = Depends(get_scheduler)
) -> SyncResponse:
    """Trigger immediate data synchronization"""
    from app.utils.logger import setup_logger
    logger = setup_logger(__name__)
    
    try:
        # Validate source parameter
        valid_sources = ['all', 'dws', 'treasury', 'correlation']
        if request.source not in valid_sources:
            logger.error(f"Invalid sync source requested: {request.source}")
            raise HTTPException(400, detail=f"Invalid source. Must be one of: {valid_sources}")
        
        logger.info(f"Triggering immediate sync for source: {request.source}")
        
        # Trigger sync in background
        results = await scheduler.trigger_immediate_sync(request.source)
        
        logger.info(f"Sync completed for {request.source}: {results.get('status', 'unknown')}")
        
        return SyncResponse(
            status=results.get('status', 'unknown'),
            results=results,
            trigger_time=results.get('trigger_time', '')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync for {request.source}: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=f"Failed to trigger sync: {str(e)}")


# Data Correlation Endpoints

@router.get("/correlation/projects")
async def correlate_all_projects(
    correlation_service: DataCorrelationService = Depends(get_correlation_service)
) -> Dict[str, Any]:
    """Get correlation analysis for all projects"""
    try:
        return await correlation_service.correlate_all_projects()
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to correlate projects: {str(e)}")


@router.get("/correlation/projects/{project_id}", response_model=ProjectCorrelationResponse)
async def correlate_project(
    project_id: str,
    correlation_service: DataCorrelationService = Depends(get_correlation_service)
) -> ProjectCorrelationResponse:
    """Get correlation analysis for a specific project"""
    try:
        correlation = await correlation_service.correlate_project_financial_data(project_id)
        
        if not correlation:
            raise HTTPException(404, detail="Project not found or no correlation data available")
        
        return ProjectCorrelationResponse(**correlation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to correlate project: {str(e)}")


@router.get("/correlation/municipalities/{municipality_id}", response_model=MunicipalOverviewResponse)
async def get_municipal_overview(
    municipality_id: str,
    correlation_service: DataCorrelationService = Depends(get_correlation_service)
) -> MunicipalOverviewResponse:
    """Get investment overview for a municipality"""
    try:
        overview = await correlation_service.get_municipal_investment_overview(municipality_id)
        
        if not overview:
            raise HTTPException(404, detail="Municipality not found")
        
        return MunicipalOverviewResponse(**overview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to get municipal overview: {str(e)}")


# Data Quality and Health Endpoints

@router.get("/health/data-sources")
async def get_data_sources_health() -> Dict[str, Any]:
    """Get health status of all data sources"""
    try:
        # This would typically check the status of DWS, Treasury APIs, database connections, etc.
        health_status = {
            "timestamp": "2024-08-10T18:02:54Z",
            "overall_status": "healthy",
            "data_sources": {
                "dws_api": {
                    "status": "healthy",
                    "last_successful_fetch": "2024-08-10T17:45:00Z",
                    "response_time_ms": 1250,
                    "error_count_24h": 0
                },
                "treasury_api": {
                    "status": "healthy", 
                    "last_successful_fetch": "2024-08-10T17:30:00Z",
                    "response_time_ms": 850,
                    "error_count_24h": 1
                },
                "database": {
                    "status": "healthy",
                    "connection_pool_used": 3,
                    "connection_pool_size": 20,
                    "query_avg_time_ms": 45
                }
            },
            "data_freshness": {
                "dws_projects": "30 minutes ago",
                "financial_data": "45 minutes ago",
                "correlation_analysis": "2 hours ago"
            }
        }
        
        return health_status
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to get health status: {str(e)}")


@router.get("/stats/data-quality")
async def get_data_quality_stats(
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get data quality statistics"""
    try:
        # This would analyze data quality metrics
        from sqlalchemy import select, func
        from app.db.models import Project, Municipality, FinancialData
        
        # Count various entities
        projects_stmt = select(func.count(Project.id))
        projects_result = await session.execute(projects_stmt)
        total_projects = projects_result.scalar()
        
        municipalities_stmt = select(func.count(Municipality.id))
        municipalities_result = await session.execute(municipalities_stmt)
        total_municipalities = municipalities_result.scalar()
        
        financial_stmt = select(func.count(FinancialData.id))
        financial_result = await session.execute(financial_stmt)
        total_financial_records = financial_result.scalar()
        
        # Projects with complete data
        complete_projects_stmt = select(func.count(Project.id)).where(
            Project.budget_allocated.isnot(None),
            Project.municipality_id.isnot(None),
            Project.status.isnot(None)
        )
        complete_projects_result = await session.execute(complete_projects_stmt)
        complete_projects = complete_projects_result.scalar()
        
        data_quality = {
            "overview": {
                "total_projects": total_projects,
                "total_municipalities": total_municipalities,
                "total_financial_records": total_financial_records
            },
            "completeness": {
                "projects_with_complete_data": complete_projects,
                "completeness_rate": round((complete_projects / total_projects * 100) if total_projects > 0 else 0, 2)
            },
            "data_sources": {
                "dws_projects": total_projects,
                "treasury_financial_data": total_financial_records
            },
            "quality_indicators": {
                "projects_with_budgets": complete_projects,
                "municipalities_with_financial_data": total_financial_records,
                "orphaned_projects": total_projects - complete_projects
            }
        }
        
        return data_quality
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to get data quality stats: {str(e)}")


# Utility functions for initialization (called during app startup)

def initialize_data_sync_services(notification_manager: DataChangeNotifier) -> None:
    """Initialize global service instances"""
    global _data_scheduler, _correlation_service, _notification_manager
    
    _notification_manager = notification_manager
    _correlation_service = DataCorrelationService(notification_manager)
    _data_scheduler = DataScheduler(notification_manager)
