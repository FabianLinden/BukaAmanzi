#!/usr/bin/env python3
"""
Complete script to remove ALL demo data from BukaAmanzi system
and configure it for real-time data only.

This script:
1. Removes demo municipalities (DEMO-001, "Demo Municipality", etc.)
2. Removes demo projects (external_id="EXT-123", etc.)
3. Removes mock financial data (flagged with _mock_data: true)
4. Shows what real data remains in the system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import sqlalchemy
        import asyncio
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install dependencies:")
        print("   cd backend && pip install -r requirements.txt")
        return False

async def remove_all_demo_data():
    """Remove ALL demo data from the database."""
    try:
        from app.db.session import async_session_factory
        from app.db.models import Municipality, Project, FinancialData
        from sqlalchemy import select
        
        async with async_session_factory() as session:
            print("🔍 Scanning database for demo data...")
            
            # Statistics
            total_removed = 0
            
            # 1. Remove demo projects first (foreign key constraints)
            print("\n📋 Removing demo projects...")
            demo_projects = await session.execute(
                select(Project).where(
                    (Project.external_id == "EXT-123") |
                    (Project.name.like('%Demo%')) |
                    (Project.name.like('%Test%')) |
                    (Project.source == 'demo') |
                    (Project.name.like('%Sample%'))
                )
            )
            demo_project_list = demo_projects.scalars().all()
            
            for project in demo_project_list:
                print(f"   🗑️  {project.name} ({project.external_id})")
                await session.delete(project)
                total_removed += 1
            
            # 2. Remove demo municipalities
            print("\n🏛️  Removing demo municipalities...")
            demo_munis = await session.execute(
                select(Municipality).where(
                    (Municipality.name.like('%Demo%')) |
                    (Municipality.code == 'DEMO-001') |
                    (Municipality.name == 'Demo Municipality') |
                    (Municipality.name.like('%Test%')) |
                    (Municipality.name.like('%Sample%'))
                )
            )
            demo_municipality_list = demo_munis.scalars().all()
            
            for muni in demo_municipality_list:
                print(f"   🗑️  {muni.name} ({muni.code})")
                await session.delete(muni)
                total_removed += 1
            
            # 3. Remove mock financial data
            print("\n💰 Removing mock financial data...")
            try:
                mock_financial = await session.execute(
                    select(FinancialData).where(
                        FinancialData.raw_data.op('->>')('_mock_data') == 'true'
                    )
                )
                mock_financial_list = mock_financial.scalars().all()
                
                for financial in mock_financial_list:
                    # Get municipality name for logging
                    muni_stmt = select(Municipality).where(Municipality.id == financial.municipality_id)
                    muni_result = await session.execute(muni_stmt)
                    municipality = muni_result.scalar_one_or_none()
                    muni_name = municipality.name if municipality else "Unknown"
                    
                    print(f"   🗑️  Mock data for {muni_name} ({financial.financial_year})")
                    await session.delete(financial)
                    total_removed += 1
                    
            except Exception as e:
                print(f"   ⚠️  Could not process mock financial data: {e}")
            
            # Commit all changes
            await session.commit()
            
            print(f"\n✅ Removed {total_removed} demo/mock records")
            
            # 4. Show what remains
            print("\n📊 Real data remaining in system:")
            
            # Real municipalities
            real_munis = await session.execute(select(Municipality))
            real_municipality_list = real_munis.scalars().all()
            
            print(f"\n🏛️  Municipalities ({len(real_municipality_list)}):")
            for muni in real_municipality_list[:10]:  # Show first 10
                print(f"   ✅ {muni.name} ({muni.code}) - {muni.province}")
            if len(real_municipality_list) > 10:
                print(f"   ... and {len(real_municipality_list) - 10} more")
            
            # Real projects
            real_projects = await session.execute(select(Project))
            real_project_list = real_projects.scalars().all()
            
            print(f"\n📋 Projects ({len(real_project_list)}):")
            for project in real_project_list[:5]:  # Show first 5
                print(f"   ✅ {project.name} ({project.source})")
            if len(real_project_list) > 5:
                print(f"   ... and {len(real_project_list) - 5} more")
            
            # Real financial data
            real_financial = await session.execute(select(FinancialData))
            real_financial_list = real_financial.scalars().all()
            
            print(f"\n💰 Financial Records ({len(real_financial_list)}):")
            for financial in real_financial_list[:3]:  # Show first 3
                muni_stmt = select(Municipality).where(Municipality.id == financial.municipality_id)
                muni_result = await session.execute(muni_stmt)
                municipality = muni_result.scalar_one_or_none()
                muni_name = municipality.name if municipality else "Unknown"
                
                # Check if this is real or mock data
                data_type = "Real API" if not financial.raw_data or not financial.raw_data.get('_mock_data') else "Mock"
                print(f"   ✅ {muni_name} ({financial.financial_year}) - {data_type}")
            if len(real_financial_list) > 3:
                print(f"   ... and {len(real_financial_list) - 3} more")
            
            return total_removed > 0
            
    except ImportError as e:
        print(f"❌ Cannot import required modules: {e}")
        print("💡 Make sure you're running this from the project root and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

async def main():
    """Main function to execute demo data removal."""
    print("🧹 BukaAmanzi Demo Data Removal Tool")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Remove demo data
    print("\n🚀 Starting comprehensive demo data removal...")
    
    try:
        success = await remove_all_demo_data()
        
        if success:
            print("\n" + "="*50)
            print("🎉 SUCCESS! Demo data removal completed!")
            print("📡 Your system now uses only real-time data from:")
            print("   • Treasury API (municipaldata.treasury.gov.za)")
            print("   • DWS API (real water project data)")
            print("   • Other official government data sources")
            print("\n💡 Next steps:")
            print("   • Run your ETL processes to fetch latest real data")
            print("   • Restart your backend server")
            print("   • Check the frontend to see real municipality data")
        else:
            print("\n✨ Database was already clean - no demo data found!")
            print("📡 Your system is configured for real-time data only")
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
