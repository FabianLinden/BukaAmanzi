from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Municipality, Project


async def seed_database(session: AsyncSession) -> dict:
    """Seed minimal demo data for development if empty.

    Returns a dict with created ids.
    """
    created = {}

    result = await session.execute(select(Municipality).limit(1))
    any_muni = result.scalar_one_or_none()

    if not any_muni:
        muni_id = str(uuid.uuid4())
        municipality = Municipality(
            id=muni_id,
            name="Demo Municipality",
            code="DEMO-001",
            province="Gauteng",
            project_count=1,
            total_value=1_000_000.0,
            dashboard_url="https://example.org/demo",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(municipality)
        created["municipality_id"] = muni_id

        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            external_id="EXT-123",
            source="municipal_money",
            municipality_id=muni_id,
            name="Water Pipeline Upgrade",
            description="Upgrade of main pipeline section",
            project_type="pipeline",
            status="in_progress",
            progress_percentage=10,
            contractor="Amanzi Builders",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(project)
        created["project_id"] = project_id

        await session.commit()
    else:
        # find a project to update later
        result = await session.execute(select(Project).limit(1))
        p = result.scalar_one_or_none()
        if p:
            created["project_id"] = p.id
        result = await session.execute(select(Municipality).limit(1))
        m = result.scalar_one_or_none()
        if m:
            created["municipality_id"] = m.id

    return created


