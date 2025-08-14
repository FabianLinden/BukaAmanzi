from typing import Any, List, Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Report, Contributor, Project, Municipality, FinancialData
from app.db.session import get_db_session
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


class ContributorIn(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None


class ReportIn(BaseModel):
    project_id: str
    title: str
    description: str
    location: Optional[str] = None
    address: Optional[str] = None
    report_type: str  # 'progress_update', 'issue', 'completion', 'quality_concern'
    contributor_name: Optional[str] = None
    contributor: Optional[ContributorIn] = None
    photos: Optional[List[str]] = None


class ReportOut(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    location: Optional[str] = None
    address: Optional[str] = None
    report_type: str
    status: str
    upvotes: int
    downvotes: int
    photos: Optional[List[str]] = None
    contributor_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContributorOut(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/summary")
async def get_reports_summary(
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get summary statistics for the water infrastructure monitoring system."""
    try:
        # Get project counts
        projects_stmt = select(func.count(Project.id))
        projects_result = await session.execute(projects_stmt)
        total_projects = projects_result.scalar()

        # Get municipality counts
        municipalities_stmt = select(func.count(Municipality.id))
        municipalities_result = await session.execute(municipalities_stmt)
        total_municipalities = municipalities_result.scalar()

        # Get financial data counts
        financial_stmt = select(func.count(FinancialData.id))
        financial_result = await session.execute(financial_stmt)
        total_financial_records = financial_result.scalar()

        # Get report counts
        reports_stmt = select(func.count(Report.id))
        reports_result = await session.execute(reports_stmt)
        total_reports = reports_result.scalar()

        # Get project status breakdown
        status_stmt = select(Project.status, func.count(Project.id)).group_by(Project.status)
        status_result = await session.execute(status_stmt)
        status_breakdown = {status: count for status, count in status_result.fetchall()}

        # Calculate total budget
        budget_stmt = select(func.sum(Project.budget_allocated))
        budget_result = await session.execute(budget_stmt)
        total_budget = budget_result.scalar() or 0.0

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_overview": {
                "total_projects": total_projects,
                "total_municipalities": total_municipalities,
                "total_financial_records": total_financial_records,
                "total_reports": total_reports,
                "total_budget_allocated": total_budget
            },
            "project_status": status_breakdown,
            "data_sources": {
                "dws": {"status": "active", "projects": total_projects},
                "treasury": {"status": "active", "financial_records": total_financial_records}
            }
        }

    except Exception as e:
        logger.error(f"Error generating reports summary: {str(e)}")
        raise HTTPException(500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/", response_model=List[ReportOut])
async def list_reports(
    project_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    report_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """List community reports with filtering and pagination."""
    filters = []
    
    if project_id:
        filters.append(Report.project_id == project_id)
    if status:
        filters.append(Report.status == status)
    if report_type:
        filters.append(Report.report_type == report_type)

    stmt = select(Report).where(and_(*filters)) if filters else select(Report)
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    
    result = await session.execute(stmt)
    reports = result.scalars().all()
    
    # Convert photos from JSON to list for response
    report_list = []
    for report in reports:
        report_dict = {
            "id": report.id,
            "project_id": report.project_id,
            "title": report.title,
            "description": report.description,
            "location": report.location,
            "address": report.address,
            "report_type": report.report_type,
            "status": report.status,
            "upvotes": report.upvotes,
            "downvotes": report.downvotes,
            "photos": report.photos.get("photos", []) if report.photos else None,
            "contributor_name": report.contributor_name,
            "created_at": report.created_at,
        }
        report_list.append(report_dict)
    
    return report_list


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Get detailed report information."""
    stmt = select(Report).where(Report.id == report_id)
    result = await session.execute(stmt)
    report = result.scalar_one_or_none()
    
    if report is None:
        raise HTTPException(404, detail="Report not found")
    
    return ReportOut(
        id=report.id,
        project_id=report.project_id,
        title=report.title,
        description=report.description,
        location=report.location,
        address=report.address,
        report_type=report.report_type,
        status=report.status,
        upvotes=report.upvotes,
        downvotes=report.downvotes,
        photos=report.photos.get("photos", []) if report.photos else None,
        contributor_name=report.contributor_name,
        created_at=report.created_at,
    )


@router.post("/", response_model=ReportOut)
async def create_report(
    report_data: ReportIn,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Create a new community report."""
    contributor_id = None
    
    # Create contributor if provided
    if report_data.contributor:
        contributor = Contributor(
            id=str(uuid4()),
            name=report_data.contributor.name,
            email=report_data.contributor.email,
            organization=report_data.contributor.organization,
            created_at=datetime.utcnow(),
        )
        session.add(contributor)
        contributor_id = contributor.id
    
    # Create report
    report = Report(
        id=str(uuid4()),
        contributor_id=contributor_id,
        project_id=report_data.project_id,
        title=report_data.title,
        description=report_data.description,
        location=report_data.location,
        address=report_data.address,
        report_type=report_data.report_type,
        status="published",
        upvotes=0,
        downvotes=0,
        photos={"photos": report_data.photos} if report_data.photos else None,
        contributor_name=report_data.contributor_name,
        created_at=datetime.utcnow(),
    )
    
    session.add(report)
    await session.commit()
    await session.refresh(report)
    
    logger.info(f"Created new report: {report.id} for project: {report.project_id}")
    
    return ReportOut(
        id=report.id,
        project_id=report.project_id,
        title=report.title,
        description=report.description,
        location=report.location,
        address=report.address,
        report_type=report.report_type,
        status=report.status,
        upvotes=report.upvotes,
        downvotes=report.downvotes,
        photos=report.photos.get("photos", []) if report.photos else None,
        contributor_name=report.contributor_name,
        created_at=report.created_at,
    )


@router.post("/{report_id}/vote")
async def vote_on_report(
    report_id: str,
    vote_type: str = Query(..., regex="^(up|down)$"),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Vote on a community report."""
    stmt = select(Report).where(Report.id == report_id)
    result = await session.execute(stmt)
    report = result.scalar_one_or_none()
    
    if report is None:
        raise HTTPException(404, detail="Report not found")
    
    if vote_type == "up":
        report.upvotes += 1
    else:  # down
        report.downvotes += 1
    
    await session.commit()
    
    return {
        "status": "success",
        "upvotes": report.upvotes,
        "downvotes": report.downvotes
    }
