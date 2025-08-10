from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Municipality
from app.db.session import get_db_session
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ProjectOut(BaseModel):
    id: str
    external_id: Optional[str] = None
    source: str
    municipality_id: Optional[str] = None
    municipality_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    address: Optional[str] = None
    budget_allocated: Optional[float] = None
    budget_spent: Optional[float] = None
    progress_percentage: int
    contractor: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSummaryOut(BaseModel):
    id: str
    name: str
    municipality_name: Optional[str] = None
    status: str
    progress_percentage: int
    budget_allocated: Optional[float] = None
    budget_spent: Optional[float] = None

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    status: Optional[str] = Query(default=None),
    municipality_id: Optional[str] = Query(default=None),
    project_type: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Search in project name, description, or contractor"),
    min_progress: Optional[int] = Query(default=None, ge=0, le=100),
    max_progress: Optional[int] = Query(default=None, ge=0, le=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """List projects with advanced filtering and search capabilities."""
    filters = []
    
    if status:
        filters.append(Project.status == status)
    if municipality_id:
        filters.append(Project.municipality_id == municipality_id)
    if project_type:
        filters.append(Project.project_type == project_type)
    if min_progress is not None:
        filters.append(Project.progress_percentage >= min_progress)
    if max_progress is not None:
        filters.append(Project.progress_percentage <= max_progress)
    
    # Join with Municipality for enhanced data
    stmt = select(Project, Municipality).outerjoin(Municipality, Project.municipality_id == Municipality.id)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # Add search functionality
    if search:
        search_term = f"%{search}%"
        search_filters = [
            Project.name.ilike(search_term),
            Project.description.ilike(search_term),
            Project.contractor.ilike(search_term)
        ]
        stmt = stmt.where(and_(*filters, or_(*search_filters))) if filters else stmt.where(or_(*search_filters))
    
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await session.execute(stmt)
    rows = result.all()
    
    # Transform results to include municipality name
    projects = []
    for project, municipality in rows:
        project_dict = {
            "id": project.id,
            "external_id": project.external_id,
            "source": project.source,
            "municipality_id": project.municipality_id,
            "municipality_name": municipality.name if municipality else None,
            "name": project.name,
            "description": project.description,
            "project_type": project.project_type,
            "status": project.status,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "location": project.location,
            "address": project.address,
            "budget_allocated": project.budget_allocated,
            "budget_spent": project.budget_spent,
            "progress_percentage": project.progress_percentage,
            "contractor": project.contractor,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        projects.append(project_dict)
    
    return projects


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        from fastapi import HTTPException

        raise HTTPException(404, detail="Project not found")
    return project

