from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Municipality, Project
from app.db.session import get_db_session


class MunicipalityOut(BaseModel):
    id: str
    name: str
    code: str
    province: Optional[str] = None
    project_count: int
    total_value: float
    dashboard_url: Optional[str] = None

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/", response_model=List[MunicipalityOut])
async def list_municipalities(
    province: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    stmt = select(Municipality)
    if province:
        stmt = stmt.where(Municipality.province == province)
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return rows


@router.get("/{municipality_id}", response_model=MunicipalityOut)
async def get_municipality(
    municipality_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    stmt = select(Municipality).where(Municipality.id == municipality_id)
    result = await session.execute(stmt)
    municipality = result.scalar_one_or_none()
    if municipality is None:
        from fastapi import HTTPException

        raise HTTPException(404, detail="Municipality not found")
    return municipality


@router.get("/{municipality_id}/projects")
async def get_municipality_projects(
    municipality_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = (
        select(Project)
        .where(Project.municipality_id == municipality_id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return rows

