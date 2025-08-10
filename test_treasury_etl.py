#!/usr/bin/env python3
"""
Test script for Treasury ETL functionality
This script can be run independently to test the Treasury ETL fixes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import logging
from datetime import datetime
from app.etl.treasury import MunicipalTreasuryETL
from app.db.session import init_db, async_session_factory
from app.db.models import Municipality, FinancialData
from sqlalchemy import select

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockNotifier:
    """Mock notification manager for testing"""
    
    async def notify_change(self, data):
        logger.info(f"Change notification: {data}")
    
    async def notify_system_error(self, title, message):
        logger.error(f"System error: {title} - {message}")

async def create_test_municipalities():
    """Create test municipalities if they don't exist"""
    async with async_session_factory() as session:
        test_municipalities = [
            {"code": "CPT", "name": "City of Cape Town", "province": "Western Cape"},
            {"code": "ETH", "name": "eThekwini Municipality", "province": "KwaZulu-Natal"},
            {"code": "JHB", "name": "City of Johannesburg", "province": "Gauteng"},
            {"code": "DEMO-001", "name": "Demo Municipality", "province": "Test Province"},
            {"code": "MP311", "name": "City of Mbombela", "province": "Mpumalanga"},
        ]
        
        for muni_data in test_municipalities:
            # Check if municipality exists
            stmt = select(Municipality).where(Municipality.code == muni_data["code"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                from uuid import uuid4
                municipality = Municipality(
                    id=str(uuid4()),
                    name=muni_data["name"],
                    code=muni_data["code"],
                    province=muni_data["province"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(municipality)
                logger.info(f"Created test municipality: {municipality.name}")
        
        await session.commit()

async def check_financial_data():
    """Check existing financial data"""
    async with async_session_factory() as session:
        stmt = select(FinancialData).join(Municipality)
        result = await session.execute(stmt)
        financial_records = result.scalars().all()
        
        logger.info(f"Found {len(financial_records)} existing financial data records")
        
        for record in financial_records:
            # Get municipality
            stmt = select(Municipality).where(Municipality.id == record.municipality_id)
            muni_result = await session.execute(stmt)
            municipality = muni_result.scalar_one()
            
            logger.info(
                f"  {municipality.name} ({municipality.code}): "
                f"Budget R{record.total_budget/1e6:.1f}M, "
                f"Water R{record.water_related_capex/1e6:.1f}M"
            )

async def test_treasury_etl():
    """Test Treasury ETL functionality"""
    
    logger.info("=" * 60)
    logger.info("TESTING TREASURY ETL FUNCTIONALITY")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        logger.info("1. Initializing database...")
        await init_db()
        
        # Create test municipalities
        logger.info("2. Creating test municipalities...")
        await create_test_municipalities()
        
        # Check existing data
        logger.info("3. Checking existing financial data...")
        await check_financial_data()
        
        # Initialize ETL
        logger.info("4. Initializing Treasury ETL...")
        mock_notifier = MockNotifier()
        
        async with MunicipalTreasuryETL(mock_notifier) as etl:
            logger.info("5. Testing financial data sync...")
            
            # Test individual municipality sync
            test_municipality_code = "DEMO-001"
            logger.info(f"   Testing financial data fetch for {test_municipality_code}...")
            
            financial_data = await etl.fetch_financial_data(test_municipality_code, 2024)
            logger.info(f"   Fetched data: Budget R{financial_data['total_budget']/1e6:.1f}M")
            
            # Store the data
            logger.info("   Storing financial data...")
            record_id = await etl.store_financial_data(financial_data)
            
            if record_id:
                logger.info(f"   ✅ Successfully stored financial data with ID: {record_id}")
            else:
                logger.warning("   ⚠️  Failed to store financial data")
            
            # Test full sync
            logger.info("6. Testing full financial data sync...")
            synced_records = await etl.sync_all_financial_data(2024)
            logger.info(f"   ✅ Synced {len(synced_records)} financial records")
            
            # Test change detection polling
            logger.info("7. Testing change detection polling...")
            await etl.poll_with_change_detection()
            logger.info("   ✅ Change detection polling completed")
        
        # Final check of data
        logger.info("8. Final check of financial data...")
        await check_financial_data()
        
        logger.info("=" * 60)
        logger.info("✅ TREASURY ETL TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        
        # Summary
        async with async_session_factory() as session:
            # Count municipalities
            stmt = select(Municipality)
            result = await session.execute(stmt)
            municipalities = result.scalars().all()
            
            # Count financial data
            stmt = select(FinancialData)
            result = await session.execute(stmt)
            financial_records = result.scalars().all()
            
            logger.info(f"Summary:")
            logger.info(f"  - Municipalities: {len(municipalities)}")
            logger.info(f"  - Financial records: {len(financial_records)}")
            
            # Show recent financial data
            if financial_records:
                recent_record = max(financial_records, key=lambda x: x.updated_at)
                stmt = select(Municipality).where(Municipality.id == recent_record.municipality_id)
                muni_result = await session.execute(stmt)
                municipality = muni_result.scalar_one()
                
                logger.info(f"  - Most recent update: {municipality.name}")
                logger.info(f"    Budget: R{recent_record.total_budget/1e6:.1f}M")
                logger.info(f"    Water investment: R{recent_record.water_related_capex/1e6:.1f}M")
                logger.info(f"    Updated: {recent_record.updated_at}")
        
    except Exception as e:
        logger.error(f"❌ Treasury ETL test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

async def main():
    """Main test function"""
    try:
        await test_treasury_etl()
        logger.info("🎉 All tests passed! Treasury ETL is working correctly.")
    except Exception as e:
        logger.error(f"💥 Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
