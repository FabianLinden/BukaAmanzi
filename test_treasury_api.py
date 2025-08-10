#!/usr/bin/env python3
"""
Test Treasury API endpoints and fetch real financial data
"""

import asyncio
import sys
import json
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx
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
    """Mock notification manager"""
    async def notify_change(self, data):
        logger.info(f"Change notification: {data}")
    async def notify_system_error(self, title, message):
        logger.error(f"System error: {title} - {message}")

async def test_treasury_api_endpoints():
    """Test different Treasury API endpoints to find working ones"""
    
    base_urls = [
        "https://municipaldata.treasury.gov.za/api",
        "https://municipaldata.treasury.gov.za/api/v1",
        "http://municipaldata.treasury.gov.za/api"
    ]
    
    test_endpoints = [
        "/cubes",
        "/cubes/municipalities/facts",
        "/cubes/budget_actual/facts",
        "/cubes/capital/facts"
    ]
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for base_url in base_urls:
            logger.info(f"\n=== Testing base URL: {base_url} ===")
            
            for endpoint in test_endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    logger.info(f"Testing: {url}")
                    response = await client.get(url)
                    logger.info(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"  ✅ SUCCESS - JSON response with {len(str(data))} characters")
                            if isinstance(data, dict):
                                logger.info(f"  Keys: {list(data.keys())}")
                        except Exception as e:
                            logger.info(f"  ⚠️  Non-JSON response: {str(e)}")
                    else:
                        logger.info(f"  ❌ Failed with status {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"  💥 Request failed: {str(e)}")

async def test_specific_municipality_codes():
    """Test with specific known municipality codes"""
    
    # Known South African municipality codes
    known_municipalities = [
        ("CPT", "City of Cape Town"),
        ("ETH", "eThekwini Municipality"), 
        ("JHB", "City of Johannesburg"),
        ("TSH", "City of Tshwane"),
        ("EKU", "Ekurhuleni Metropolitan Municipality"),
        ("MAN", "Mangaung Metropolitan Municipality"),
        ("BUF", "Buffalo City Metropolitan Municipality"),
        ("NMA", "Nelson Mandela Bay Municipality")
    ]
    
    base_url = "https://municipaldata.treasury.gov.za/api"
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        logger.info("\n=== Testing with known municipality codes ===")
        
        for code, name in known_municipalities:
            logger.info(f"\nTesting {name} ({code}):")
            
            # Test different year formats and parameters
            test_configs = [
                {
                    'endpoint': '/cubes/budget_actual/facts',
                    'params': {
                        'cut': f'municipality.code:"{code}"|financial_year_end.year:2023',
                        'drilldown': 'item.code',
                        'format': 'json'
                    }
                },
                {
                    'endpoint': '/cubes/budget_actual/facts', 
                    'params': {
                        'cut': f'municipality.code:"{code}"',
                        'drilldown': 'financial_year_end.year|item.code',
                        'format': 'json'
                    }
                },
                {
                    'endpoint': '/cubes/capital/facts',
                    'params': {
                        'cut': f'municipality.code:"{code}"|financial_year_end.year:2023',
                        'format': 'json'
                    }
                }
            ]
            
            for config in test_configs:
                url = f"{base_url}{config['endpoint']}"
                try:
                    response = await client.get(url, params=config['params'])
                    logger.info(f"  {config['endpoint']}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            cells = data.get('cells', [])
                            logger.info(f"    ✅ SUCCESS: {len(cells)} data cells returned")
                            
                            if cells:
                                # Show sample data structure
                                sample = cells[0]
                                logger.info(f"    Sample keys: {list(sample.keys())}")
                                break
                                
                        except Exception as e:
                            logger.error(f"    JSON parse error: {e}")
                    else:
                        logger.info(f"    Status: {response.status_code}")
                        if response.status_code != 500:  # Don't log 500 details
                            logger.info(f"    Response: {response.text[:200]}...")
                            
                except Exception as e:
                    logger.error(f"    Request error: {e}")

async def fetch_real_financial_data_improved():
    """Improved method to fetch real financial data"""
    
    logger.info("\n=== ATTEMPTING TO FETCH REAL FINANCIAL DATA ===")
    
    # Initialize database
    await init_db()
    
    # Create or get municipalities
    async with async_session_factory() as session:
        # Try Cape Town first (most likely to have data)
        stmt = select(Municipality).where(Municipality.code == "CPT")
        result = await session.execute(stmt)
        cpt = result.scalar_one_or_none()
        
        if not cpt:
            from uuid import uuid4
            cpt = Municipality(
                id=str(uuid4()),
                name="City of Cape Town",
                code="CPT", 
                province="Western Cape",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(cpt)
            await session.commit()
            logger.info("Created City of Cape Town municipality")
    
    # Try multiple approaches to get real data
    approaches = [
        {
            'name': 'Latest available year with basic parameters',
            'url': 'https://municipaldata.treasury.gov.za/api/cubes/budget_actual/facts',
            'params': {
                'cut': 'municipality.code:"CPT"',
                'drilldown': 'financial_year_end.year|item.code',
                'format': 'json'
            }
        },
        {
            'name': '2023 budget data with detailed breakdown',
            'url': 'https://municipaldata.treasury.gov.za/api/cubes/budget_actual/facts',
            'params': {
                'cut': 'municipality.code:"CPT"|financial_year_end.year:2023',
                'drilldown': 'item.code|amount_type.label',
                'format': 'json'
            }
        },
        {
            'name': '2022 budget data (older, more stable)',
            'url': 'https://municipaldata.treasury.gov.za/api/cubes/budget_actual/facts',
            'params': {
                'cut': 'municipality.code:"CPT"|financial_year_end.year:2022',
                'drilldown': 'item.code|amount_type.label',
                'format': 'json'
            }
        },
        {
            'name': 'Capital expenditure data',
            'url': 'https://municipaldata.treasury.gov.za/api/cubes/capital/facts',
            'params': {
                'cut': 'municipality.code:"CPT"|financial_year_end.year:2023',
                'drilldown': 'item.label',
                'format': 'json'
            }
        }
    ]
    
    mock_notifier = MockNotifier()
    
    async with MunicipalTreasuryETL(mock_notifier) as etl:
        
        for approach in approaches:
            logger.info(f"\nTrying approach: {approach['name']}")
            
            try:
                response = await etl.session.get(approach['url'], params=approach['params'])
                logger.info(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    cells = data.get('cells', [])
                    
                    if cells:
                        logger.info(f"✅ SUCCESS: Found {len(cells)} data records!")
                        
                        # Process and show sample data
                        logger.info("Sample records:")
                        for i, cell in enumerate(cells[:3]):
                            logger.info(f"  Record {i+1}: {json.dumps(cell, indent=4)}")
                        
                        # Try to process this real data
                        financial_data = etl._process_financial_data("CPT", 2023, {'cells': cells}, {'cells': []})
                        
                        logger.info(f"Processed financial data:")
                        logger.info(f"  Total Budget: R{financial_data['total_budget']/1e6:.1f}M")
                        logger.info(f"  Total Actual: R{financial_data['total_actual']/1e6:.1f}M") 
                        logger.info(f"  Water Related: R{financial_data['water_related_capex']/1e6:.1f}M")
                        
                        # Store the real data
                        record_id = await etl.store_financial_data(financial_data)
                        if record_id:
                            logger.info(f"✅ Successfully stored real financial data with ID: {record_id}")
                            return True
                        else:
                            logger.warning("Failed to store financial data")
                    
                    else:
                        logger.info("No data cells in response")
                
                elif response.status_code == 404:
                    logger.info("Endpoint not found - trying next approach")
                    
                elif response.status_code == 500:
                    logger.info("Server error - trying next approach")
                    
                else:
                    logger.info(f"Unexpected status: {response.text[:200]}")
            
            except Exception as e:
                logger.error(f"Error with approach: {e}")
                continue
        
        logger.warning("⚠️  All approaches failed - API may be down or restructured")
        return False

async def verify_stored_data():
    """Verify that data was properly stored and can be retrieved"""
    
    logger.info("\n=== VERIFYING STORED DATA ===")
    
    async with async_session_factory() as session:
        # Get all financial records
        stmt = select(FinancialData).join(Municipality).order_by(FinancialData.updated_at.desc())
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        logger.info(f"Found {len(records)} financial records in database")
        
        for record in records:
            # Get municipality
            stmt = select(Municipality).where(Municipality.id == record.municipality_id)
            muni_result = await session.execute(stmt)
            municipality = muni_result.scalar_one()
            
            logger.info(f"\n📊 {municipality.name} ({municipality.code}) - {record.financial_year}")
            logger.info(f"   Budget: R{record.total_budget/1e6:.1f}M")
            logger.info(f"   Actual: R{record.total_actual/1e6:.1f}M") 
            logger.info(f"   Water Investment: R{record.water_related_capex/1e6:.1f}M")
            logger.info(f"   Infrastructure: R{record.infrastructure_budget/1e6:.1f}M")
            logger.info(f"   Budget Variance: {record.budget_variance:.1f}%")
            logger.info(f"   Updated: {record.updated_at}")
            
            # Check if this is real vs mock data
            if record.raw_data and record.raw_data.get('_mock_data'):
                logger.info(f"   📝 Type: Mock data (generated at {record.raw_data.get('_generated_at')})")
            else:
                logger.info(f"   🌐 Type: Real API data")
        
        return len(records)

async def main():
    """Main function to test Treasury API and data fetching"""
    
    logger.info("🚀 Starting Treasury API real data test...")
    
    try:
        # Step 1: Test API endpoints
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Testing Treasury API endpoints")
        logger.info("="*60)
        await test_treasury_api_endpoints()
        
        # Step 2: Test with specific municipalities
        logger.info("\n" + "="*60) 
        logger.info("STEP 2: Testing with known municipality codes")
        logger.info("="*60)
        await test_specific_municipality_codes()
        
        # Step 3: Attempt to fetch and store real data
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Fetching and storing real financial data")  
        logger.info("="*60)
        success = await fetch_real_financial_data_improved()
        
        # Step 4: Verify stored data
        logger.info("\n" + "="*60)
        logger.info("STEP 4: Verifying stored data")
        logger.info("="*60)
        record_count = await verify_stored_data()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        
        if success:
            logger.info("✅ Successfully fetched and stored real Treasury data!")
        else:
            logger.info("⚠️  Unable to fetch real data - using mock data fallback")
            
        logger.info(f"📊 Total financial records in database: {record_count}")
        logger.info("🎉 Treasury data sync test completed!")
        
    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
