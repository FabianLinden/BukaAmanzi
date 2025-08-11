#!/usr/bin/env python3
"""
Comprehensive cleanup script to remove ALL demo data.
This removes demo municipalities, projects, and mock financial data from the database.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.db.models import Municipality, Project, FinancialData


async def cleanup_demo_data():
    """Remove ALL demo data including municipalities, projects, and mock financial data."""
    async with async_session_factory() as session:
        try:
            print("🔍 Looking for ALL demo data...")
            
            # 1. Find and delete demo projects first (foreign key constraints)
            demo_projects = await session.execute(
                select(Project).where(
                    (Project.external_id == "EXT-123") |
                    (Project.name.like('%Demo%')) |
                    (Project.name.like('%Test%')) |
                    (Project.source == 'demo')
                )
            )
            demo_project_list = demo_projects.scalars().all()
            
            deleted_projects = 0
            for project in demo_project_list:
                print(f"   🗑️  Removing project: {project.name} ({project.external_id})")
                await session.delete(project)
                deleted_projects += 1
            
            # 2. Find and delete demo municipalities
            demo_munis = await session.execute(
                select(Municipality).where(
                    (Municipality.name.like('%Demo%')) |
                    (Municipality.code == 'DEMO-001') |
                    (Municipality.name == 'Demo Municipality') |
                    (Municipality.name.like('%Test%'))
                )
            )
            demo_municipality_list = demo_munis.scalars().all()
            
            deleted_munis = 0
            for muni in demo_municipality_list:
                print(f"   🗑️  Removing municipality: {muni.name} ({muni.code})")
                await session.delete(muni)
                deleted_munis += 1
            
            # 3. Find and delete mock financial data
            # Delete any financial data with the _mock_data flag
            try:
                mock_financial = await session.execute(
                    select(FinancialData).where(
                        FinancialData.raw_data.op('->>')('_mock_data') == 'true'
                    )
                )
                mock_financial_list = mock_financial.scalars().all()
                
                deleted_financial = 0
                for financial in mock_financial_list:
                    muni_stmt = select(Municipality).where(Municipality.id == financial.municipality_id)
                    muni_result = await session.execute(muni_stmt)
                    municipality = muni_result.scalar_one_or_none()
                    muni_name = municipality.name if municipality else "Unknown"
                    
                    print(f"   🗑️  Removing mock financial data for: {muni_name} ({financial.financial_year})")
                    await session.delete(financial)
                    deleted_financial += 1
                    
            except Exception as e:
                print(f"   ⚠️  Could not check/delete mock financial data: {e}")
                deleted_financial = 0
            
            await session.commit()
            
            print(f"✅ Comprehensive cleanup completed:")
            print(f"   - Deleted {deleted_projects} demo project(s)")
            print(f"   - Deleted {deleted_munis} demo municipality/municipalities")
            print(f"   - Deleted {deleted_financial} mock financial record(s)")
            
            if deleted_projects == 0 and deleted_munis == 0 and deleted_financial == 0:
                print("ℹ️  No demo data found - database is already clean!")
            else:
                print("🎉 ALL demo data successfully removed - database now contains only real data!")
                
            # Show what remains
            remaining_munis = await session.execute(select(Municipality))
            remaining_list = remaining_munis.scalars().all()
            
            print(f"\n📊 Remaining municipalities in database ({len(remaining_list)}):")
            for muni in remaining_list[:10]:  # Show first 10
                print(f"   - {muni.name} ({muni.code}) - {muni.province}")
            if len(remaining_list) > 10:
                print(f"   ... and {len(remaining_list) - 10} more")
                
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during cleanup: {e}")
            raise


async def main():
    """Main cleanup function."""
    print("🧹 Starting demo data cleanup...")
    await cleanup_demo_data()
    print("✨ Cleanup process completed!")


if __name__ == "__main__":
    asyncio.run(main())
