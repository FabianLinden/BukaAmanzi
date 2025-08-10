from fastapi import APIRouter

from .endpoints.municipalities import router as municipalities_router
from .endpoints.projects import router as projects_router
from .endpoints.etl import router as etl_router
from .endpoints.reports import router as reports_router
from .endpoints.budgets import router as budgets_router
from .endpoints.data_sync import router as data_sync_router


api_router = APIRouter()
api_router.include_router(municipalities_router, prefix="/municipalities", tags=["municipalities"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(etl_router, prefix="/etl", tags=["etl"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(budgets_router, prefix="/budgets", tags=["budgets"])
api_router.include_router(data_sync_router, prefix="/data", tags=["data-sync", "correlation", "scheduler"])

