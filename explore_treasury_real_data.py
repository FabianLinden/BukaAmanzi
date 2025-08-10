#!/usr/bin/env python3
"""
Explore successful Treasury API endpoints and work with real data
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
from app.db.session import init_db, async_session_factory
from app.db.models import Municipality, FinancialData
from sqlalchemy import select
from uuid import uuid4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def explore_cubes_endpoint():
    """Explore the /cubes endpoint to see available data cubes"""
    
    logger.info("🔍 Exploring available data cubes...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get("https://municipaldata.treasury.gov.za/api/cubes")
            if response.status_code == 200:
                data = response.json()
                
                logger.info("Available data cubes:")
                cubes = data.get('data', [])
                
                for cube in cubes:
                    logger.info(f"  📊 {cube.get('name', 'Unknown')} - {cube.get('label', 'No description')}")
                
                return cubes
            else:
                logger.error(f"Failed to fetch cubes: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching cubes: {e}")
            return []

async def fetch_real_municipalities():
    """Fetch real municipalities data from the working endpoint"""
    
    logger.info("🏛️  Fetching real municipalities data...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            url = "https://municipaldata.treasury.gov.za/api/cubes/municipalities/facts"
            params = {
                'format': 'json',
                'page_size': 100  # Get first 100 municipalities
            }
            
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                total_count = data.get('total_fact_count', 0)
                municipalities = data.get('data', [])
                
                logger.info(f"✅ Found {len(municipalities)} municipalities (Total: {total_count})")
                
                # Process and show sample municipalities
                processed_municipalities = []
                
                for i, muni in enumerate(municipalities[:10]):  # Show first 10
                    processed = {
                        'name': muni.get('municipality_name'),
                        'code': muni.get('municipality_code'),
                        'province': muni.get('province_name'), 
                        'category': muni.get('municipality_category'),
                        'demarcation_code': muni.get('demarcation_code')
                    }
                    
                    processed_municipalities.append(processed)
                    logger.info(f"  {i+1:2d}. {processed['name']} ({processed['code']}) - {processed['province']}")
                
                return processed_municipalities
                
            else:
                logger.error(f"Failed to fetch municipalities: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching municipalities: {e}")
            return []

async def test_alternative_financial_endpoints(municipality_code: str = "CPT"):
    """Test alternative endpoints that might have financial data"""
    
    logger.info(f"💰 Testing alternative financial endpoints for {municipality_code}...")
    
    # List of potential endpoints to try
    alternative_endpoints = [
        {
            'name': 'Income and Expenditure',
            'endpoint': '/cubes/incexp/facts',
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Cash Flow',  
            'endpoint': '/cubes/cashflow/facts',
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Financial Performance',
            'endpoint': '/cubes/financial_performance/facts', 
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Capital Budget',
            'endpoint': '/cubes/capital_budget/facts',
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Operating Budget',
            'endpoint': '/cubes/operating_budget/facts',
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Budget vs Actual',
            'endpoint': '/cubes/bsheet/facts',  # Balance sheet
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Aged Creditors',
            'endpoint': '/cubes/aged_creditor_facts/facts',
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        },
        {
            'name': 'Aged Debtors',
            'endpoint': '/cubes/aged_debtor_facts/facts', 
            'params': {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json'}
        }
    ]
    
    base_url = "https://municipaldata.treasury.gov.za/api"
    working_endpoints = []
    
    async with httpx.AsyncClient(timeout=30) as client:
        for endpoint_info in alternative_endpoints:
            try:
                url = f"{base_url}{endpoint_info['endpoint']}"
                logger.info(f"  Testing: {endpoint_info['name']}")
                
                response = await client.get(url, params=endpoint_info['params'])
                logger.info(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('data', [])
                    
                    if records:
                        logger.info(f"    ✅ SUCCESS: {len(records)} records found")
                        
                        # Show sample record structure
                        sample = records[0]
                        logger.info(f"    Sample keys: {list(sample.keys())[:10]}...")  # Show first 10 keys
                        
                        working_endpoints.append({
                            'name': endpoint_info['name'],
                            'endpoint': endpoint_info['endpoint'],
                            'sample_data': sample,
                            'record_count': len(records)
                        })
                    else:
                        logger.info(f"    ⚠️  No records returned")
                        
                elif response.status_code == 404:
                    logger.info(f"    ❌ Endpoint not found")
                    
                elif response.status_code == 500:
                    logger.info(f"    ❌ Server error")
                    
                else:
                    logger.info(f"    ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                logger.info(f"    💥 Error: {str(e)}")
    
    return working_endpoints

async def fetch_and_process_real_financial_data(working_endpoints, municipality_code: str = "CPT"):
    """Process real financial data from working endpoints"""
    
    logger.info(f"📊 Processing real financial data for {municipality_code}...")
    
    if not working_endpoints:
        logger.warning("No working financial endpoints found")
        return None
    
    # Combine data from all working endpoints
    combined_financial_data = {
        'municipality_code': municipality_code,
        'financial_year': datetime.now().year,
        'total_budget': 0.0,
        'total_actual': 0.0,
        'total_capex_budget': 0.0,
        'total_capex_actual': 0.0,
        'water_related_capex': 0.0,
        'infrastructure_budget': 0.0,
        'service_delivery_budget': 0.0,
        'revenue': 0.0,
        'expenditure': 0.0,
        'surplus_deficit': 0.0,
        'cash_available': 0.0,
        'budget_variance': 0.0,
        'detailed_items': [],
        '_real_data': True,
        '_data_sources': []
    }
    
    for endpoint_info in working_endpoints:
        logger.info(f"  Processing {endpoint_info['name']}...")
        
        sample_data = endpoint_info['sample_data']
        endpoint_name = endpoint_info['name'].lower()
        
        # Extract relevant financial information based on endpoint type
        try:
            if 'income' in endpoint_name or 'expenditure' in endpoint_name:
                # Process income and expenditure data
                revenue = float(sample_data.get('total_income', 0) or 0)
                expenditure = float(sample_data.get('total_expenditure', 0) or 0)
                
                combined_financial_data['revenue'] += revenue
                combined_financial_data['expenditure'] += expenditure
                combined_financial_data['surplus_deficit'] = revenue - expenditure
                
                logger.info(f"    Revenue: R{revenue/1e6:.1f}M, Expenditure: R{expenditure/1e6:.1f}M")
                
            elif 'cash' in endpoint_name:
                # Process cash flow data
                cash_available = float(sample_data.get('cash_available', 0) or 0)
                combined_financial_data['cash_available'] = cash_available
                
                logger.info(f"    Cash Available: R{cash_available/1e6:.1f}M")
                
            elif 'capital' in endpoint_name:
                # Process capital expenditure data
                capex_budget = float(sample_data.get('budget_amount', 0) or 0)
                capex_actual = float(sample_data.get('actual_amount', 0) or 0)
                
                combined_financial_data['total_capex_budget'] += capex_budget
                combined_financial_data['total_capex_actual'] += capex_actual
                
                # Check if this is water-related
                item_description = str(sample_data.get('item_description', '')).lower()
                if 'water' in item_description or 'sanitation' in item_description:
                    combined_financial_data['water_related_capex'] += capex_actual
                
                logger.info(f"    Capital Budget: R{capex_budget/1e6:.1f}M, Actual: R{capex_actual/1e6:.1f}M")
                
            # Add to detailed items
            combined_financial_data['detailed_items'].append({
                'source': endpoint_info['name'],
                'endpoint': endpoint_info['endpoint'],
                'sample_record': sample_data
            })
            
            combined_financial_data['_data_sources'].append(endpoint_info['name'])
            
        except Exception as e:
            logger.warning(f"    Error processing {endpoint_info['name']}: {e}")
    
    # Calculate totals and derived metrics
    combined_financial_data['total_budget'] = (
        combined_financial_data['total_capex_budget'] + 
        combined_financial_data['revenue']
    )
    
    combined_financial_data['total_actual'] = (
        combined_financial_data['total_capex_actual'] + 
        combined_financial_data['expenditure']
    )
    
    if combined_financial_data['total_budget'] > 0:
        combined_financial_data['budget_variance'] = (
            (combined_financial_data['total_actual'] - combined_financial_data['total_budget']) /
            combined_financial_data['total_budget'] * 100
        )
    
    # Estimate infrastructure budget (typically 20-30% of total budget)
    combined_financial_data['infrastructure_budget'] = combined_financial_data['total_budget'] * 0.25
    
    return combined_financial_data

async def store_real_financial_data(financial_data):
    """Store real financial data in the database"""
    
    logger.info("💾 Storing real financial data...")
    
    try:
        async with async_session_factory() as session:
            # Find or create municipality
            stmt = select(Municipality).where(Municipality.code == financial_data['municipality_code'])
            result = await session.execute(stmt)
            municipality = result.scalar_one_or_none()
            
            if not municipality:
                municipality = Municipality(
                    id=str(uuid4()),
                    name=f"Municipality {financial_data['municipality_code']}",
                    code=financial_data['municipality_code'],
                    province="Unknown",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(municipality)
                await session.commit()
                logger.info(f"Created municipality: {municipality.name}")
            
            # Check for existing financial data
            stmt = select(FinancialData).where(
                FinancialData.municipality_id == municipality.id,
                FinancialData.financial_year == financial_data['financial_year']
            )
            result = await session.execute(stmt)
            existing_record = result.scalar_one_or_none()
            
            if existing_record:
                # Update existing record
                existing_record.total_budget = financial_data['total_budget']
                existing_record.total_actual = financial_data['total_actual']
                existing_record.total_capex_budget = financial_data['total_capex_budget']
                existing_record.total_capex_actual = financial_data['total_capex_actual']
                existing_record.water_related_capex = financial_data['water_related_capex']
                existing_record.infrastructure_budget = financial_data['infrastructure_budget']
                existing_record.revenue = financial_data['revenue']
                existing_record.expenditure = financial_data['expenditure']
                existing_record.surplus_deficit = financial_data['surplus_deficit']
                existing_record.budget_variance = financial_data['budget_variance']
                existing_record.cash_available = financial_data['cash_available']
                existing_record.raw_data = financial_data
                existing_record.updated_at = datetime.utcnow()
                
                logger.info(f"✅ Updated existing financial record for {municipality.name}")
                
            else:
                # Create new record
                financial_record = FinancialData(
                    id=str(uuid4()),
                    municipality_id=municipality.id,
                    financial_year=financial_data['financial_year'],
                    total_budget=financial_data['total_budget'],
                    total_actual=financial_data['total_actual'],
                    total_capex_budget=financial_data['total_capex_budget'],
                    total_capex_actual=financial_data['total_capex_actual'],
                    water_related_capex=financial_data['water_related_capex'],
                    infrastructure_budget=financial_data['infrastructure_budget'],
                    service_delivery_budget=financial_data['service_delivery_budget'],
                    revenue=financial_data['revenue'],
                    expenditure=financial_data['expenditure'],
                    surplus_deficit=financial_data['surplus_deficit'],
                    budget_variance=financial_data['budget_variance'],
                    cash_available=financial_data['cash_available'],
                    raw_data=financial_data,
                    content_hash=f"real_data_{financial_data['municipality_code']}_{financial_data['financial_year']}",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(financial_record)
                
                logger.info(f"✅ Created new financial record for {municipality.name}")
            
            await session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error storing financial data: {e}")
        return False

async def main():
    """Main function to explore and fetch real Treasury data"""
    
    logger.info("🚀 Starting real Treasury data exploration and collection...")
    
    try:
        # Initialize database
        await init_db()
        
        # Step 1: Explore available cubes
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Exploring available data cubes")
        logger.info("="*60)
        cubes = await explore_cubes_endpoint()
        
        # Step 2: Fetch real municipalities
        logger.info("\n" + "="*60)
        logger.info("STEP 2: Fetching real municipalities")
        logger.info("="*60)
        municipalities = await fetch_real_municipalities()
        
        if municipalities:
            # Store real municipalities in database
            async with async_session_factory() as session:
                for muni in municipalities:
                    if muni.get('code'):
                        # Check if municipality exists
                        stmt = select(Municipality).where(Municipality.code == muni['code'])
                        result = await session.execute(stmt)
                        existing = result.scalar_one_or_none()
                        
                        if not existing:
                            municipality = Municipality(
                                id=str(uuid4()),
                                name=muni['name'] or f"Municipality {muni['code']}",
                                code=muni['code'],
                                province=muni['province'] or "Unknown",
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow(),
                            )
                            session.add(municipality)
                
                await session.commit()
                logger.info(f"✅ Stored {len(municipalities)} real municipalities in database")
        
        # Step 3: Test alternative financial endpoints
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Testing alternative financial endpoints")
        logger.info("="*60)
        working_endpoints = await test_alternative_financial_endpoints("CPT")
        
        if working_endpoints:
            logger.info(f"\n✅ Found {len(working_endpoints)} working financial endpoints:")
            for endpoint in working_endpoints:
                logger.info(f"  📊 {endpoint['name']}: {endpoint['record_count']} records")
            
            # Step 4: Process real financial data
            logger.info("\n" + "="*60)
            logger.info("STEP 4: Processing real financial data")
            logger.info("="*60)
            
            financial_data = await fetch_and_process_real_financial_data(working_endpoints, "CPT")
            
            if financial_data:
                logger.info("Real financial data summary:")
                logger.info(f"  Municipality: {financial_data['municipality_code']}")
                logger.info(f"  Total Budget: R{financial_data['total_budget']/1e6:.1f}M")
                logger.info(f"  Total Actual: R{financial_data['total_actual']/1e6:.1f}M")
                logger.info(f"  Revenue: R{financial_data['revenue']/1e6:.1f}M")
                logger.info(f"  Expenditure: R{financial_data['expenditure']/1e6:.1f}M")
                logger.info(f"  Water Investment: R{financial_data['water_related_capex']/1e6:.1f}M")
                logger.info(f"  Cash Available: R{financial_data['cash_available']/1e6:.1f}M")
                logger.info(f"  Data Sources: {', '.join(financial_data['_data_sources'])}")
                
                # Step 5: Store real data
                logger.info("\n" + "="*60)
                logger.info("STEP 5: Storing real financial data")
                logger.info("="*60)
                
                success = await store_real_financial_data(financial_data)
                if success:
                    logger.info("✅ Successfully stored real financial data!")
                else:
                    logger.error("❌ Failed to store real financial data")
            
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        
        logger.info(f"📊 Available cubes: {len(cubes)}")
        logger.info(f"🏛️  Real municipalities found: {len(municipalities)}")
        logger.info(f"💰 Working financial endpoints: {len(working_endpoints)}")
        
        if working_endpoints:
            logger.info("✅ Successfully collected and stored real Treasury data!")
            logger.info("🎯 Next step: Update ETL to use these working endpoints")
        else:
            logger.warning("⚠️  No working financial endpoints found - will continue using mock data")
        
    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
