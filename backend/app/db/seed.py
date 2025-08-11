from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Municipality, Project


async def seed_database(session: AsyncSession) -> dict:
    """Check for existing data and return references for demo functionality.
    
    No demo data is created - only real data from external sources is used.
    Returns a dict with existing ids for compatibility.
    """
    created = {}

    # Find existing projects and municipalities for demo functionality
    # but don't create any demo data
    result = await session.execute(select(Project).limit(1))
    p = result.scalar_one_or_none()
    if p:
        created["project_id"] = p.id
    
    result = await session.execute(select(Municipality).limit(1))
    m = result.scalar_one_or_none()
    if m:
        created["municipality_id"] = m.id

    return created


