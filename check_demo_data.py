#!/usr/bin/env python3
"""
Check for demo data in the database
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import async_session_factory
from app.db.models import Municipality, Project, FinancialData
from sqlalchemy import select

async def check_demo_data():
    async with async_session_factory() as session:
        print('🔍 Checking for demo data in database...')
        
        # Check for demo municipalities
        demo_munis = await session.execute(
            select(Municipality).where(
                (Municipality.name.like('%Demo%')) |
                (Municipality.code == 'DEMO-001') |
                (Municipality.name == 'Demo Municipality')
            )
        )
        demo_municipalities = demo_munis.scalars().all()
        
        print(f'Found {len(demo_municipalities)} demo municipalities:')
        for muni in demo_municipalities:
            print(f'  - {muni.name} ({muni.code})')
        
        # Check for projects with demo external_id
        demo_projects = await session.execute(
            select(Project).where(Project.external_id == 'EXT-123')
        )
        demo_project_list = demo_projects.scalars().all()
        
        print(f'Found {len(demo_project_list)} demo projects:')
        for project in demo_project_list:
            print(f'  - {project.name} (ID: {project.external_id})')
        
        # Check financial data with mock flags
        try:
            mock_financial = await session.execute(
                select(FinancialData).where(FinancialData.raw_data.op('->>')('_mock_data') == 'true')
            )
            mock_financial_list = mock_financial.scalars().all()
            print(f'Found {len(mock_financial_list)} mock financial records')
        except Exception as e:
            print(f'Could not check mock financial data: {e}')
        
        # Show all municipalities for reference
        all_munis = await session.execute(select(Municipality))
        all_municipalities = all_munis.scalars().all()
        
        print(f'\nAll municipalities in database ({len(all_municipalities)}):')
        for muni in all_municipalities:
            print(f'  - {muni.name} ({muni.code}) - {muni.province}')

if __name__ == "__main__":
    asyncio.run(check_demo_data())
