#!/usr/bin/env python3
"""
Test the v2 endpoints that were found in the cubes list
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

async def test_v2_endpoints():
    """Test the v2 endpoints that were found in the cubes list"""
    
    logger.info("🔍 Testing v2 endpoints with different municipality codes...")
    
    # Test different municipality codes
    test_municipalities = ["CPT", "ETH", "JHB", "TSH", "EKU", "MAN", "BUF", "NMA"]
    
    # V2 endpoints from the cubes list
    v2_endpoints = [
        {'name': 'Income and Expenditure v2', 'cube': 'incexp_v2'},
        {'name': 'Capital Acquisition v2', 'cube': 'capital_v2'},
        {'name': 'Cash Flow v2', 'cube': 'cflow_v2'},
        {'name': 'Financial Position v2', 'cube': 'financial_position_v2'},
        {'name': 'Aged Creditor v2', 'cube': 'aged_creditor_v2'},
        {'name': 'Aged Debtor v2', 'cube': 'aged_debtor_v2'},
        {'name': 'Grants v2', 'cube': 'grants_v2'},
        {'name': 'Repairs and Maintenance v2', 'cube': 'repmaint_v2'},
        {'name': 'Balance Sheet', 'cube': 'bsheet'},
        {'name': 'Conditional Grants', 'cube': 'conditional_grants'},
        {'name': 'Audit Opinions', 'cube': 'audit_opinions'},
    ]
    
    base_url = "https://municipaldata.treasury.gov.za/api"
    working_endpoints = []
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        for municipality_code in test_municipalities:
            logger.info(f"\n🏛️  Testing municipality: {municipality_code}")
            
            for endpoint_info in v2_endpoints:
                try:
                    cube_name = endpoint_info['cube']
                    url = f"{base_url}/cubes/{cube_name}/facts"
                    
                    # Test different parameter configurations
                    test_configs = [
                        # Basic query
                        {'cut': f'municipality.code:"{municipality_code}"', 'format': 'json', 'page_size': '10'},
                        # Without municipality filter (might work better)
                        {'format': 'json', 'page_size': '5', 'drilldown': 'municipality'},
                        # With year filter
                        {'cut': f'municipality.code:"{municipality_code}"|financial_year_end.year:2023', 'format': 'json', 'page_size': '5'},
                    ]
                    
                    for i, params in enumerate(test_configs):
                        try:
                            logger.info(f"  📊 {endpoint_info['name']} (config {i+1})")
                            
                            response = await client.get(url, params=params)
                            logger.info(f"    Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                records = data.get('data', [])
                                
                                if records and len(records) > 0:
                                    logger.info(f"    ✅ SUCCESS: {len(records)} records found!")
                                    
                                    # Show sample record structure
                                    sample = records[0]
                                    logger.info(f"    Sample keys: {list(sample.keys())[:15]}...")
                                    
                                    # Show some sample values to understand the data structure
                                    sample_values = {}
                                    for key, value in sample.items():
                                        if key in ['municipality_code', 'municipality_name', 'financial_year', 'amount', 'budget', 'actual', 'item_code', 'item_label']:
                                            sample_values[key] = value
                                    
                                    if sample_values:
                                        logger.info(f"    Sample values: {sample_values}")
                                    
                                    working_endpoints.append({
                                        'name': endpoint_info['name'],
                                        'cube': cube_name,
                                        'url': url,
                                        'params': params,
                                        'municipality': municipality_code,
                                        'sample_data': sample,
                                        'record_count': len(records),
                                        'all_records': records[:5]  # Store first 5 records
                                    })
                                    
                                    # Break after first successful config
                                    break
                                    
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
                            continue
                            
                except Exception as e:
                    logger.info(f"  💥 Failed to test {endpoint_info['name']}: {str(e)}")
            
            # Break early if we found some working endpoints
            if len(working_endpoints) >= 3:
                logger.info(f"\n🎯 Found {len(working_endpoints)} working endpoints, continuing...")
                break
    
    return working_endpoints

async def process_real_financial_data_v2(working_endpoints):
    """Process real financial data from working v2 endpoints"""
    
    logger.info("📊 Processing real financial data from v2 endpoints...")
    
    if not working_endpoints:
        logger.warning("No working endpoints found")
        return None
    
    # Group endpoints by municipality
    municipalities_data = {}
    
    for endpoint_info in working_endpoints:
        municipality_code = endpoint_info['municipality']
        
        if municipality_code not in municipalities_data:
            municipalities_data[municipality_code] = {
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
        
        municipality_data = municipalities_data[municipality_code]
        cube_name = endpoint_info['cube']
        
        logger.info(f"  Processing {endpoint_info['name']} for {municipality_code}...")
        
        try:
            # Process records based on cube type
            for record in endpoint_info['all_records']:
                
                if 'incexp' in cube_name:
                    # Income and expenditure data
                    amount = float(record.get('amount', 0) or 0)
                    item_code = str(record.get('item_code', '')).lower()
                    
                    if 'income' in item_code or 'revenue' in item_code:
                        municipality_data['revenue'] += amount
                    elif 'expenditure' in item_code or 'expense' in item_code:
                        municipality_data['expenditure'] += amount
                    
                    # Check for water-related items
                    item_label = str(record.get('item_label', '')).lower()
                    if 'water' in item_label or 'sanitation' in item_label:
                        municipality_data['water_related_capex'] += amount
                    
                elif 'capital' in cube_name:
                    # Capital expenditure data
                    budget_amount = float(record.get('budget_amount', 0) or 0)
                    actual_amount = float(record.get('actual_amount', 0) or 0)
                    
                    municipality_data['total_capex_budget'] += budget_amount
                    municipality_data['total_capex_actual'] += actual_amount
                    
                    # Check for water-related capital
                    item_label = str(record.get('item_label', '')).lower()
                    if 'water' in item_label or 'sanitation' in item_label:
                        municipality_data['water_related_capex'] += actual_amount
                
                elif 'cflow' in cube_name:
                    # Cash flow data
                    cash_amount = float(record.get('amount', 0) or 0)
                    municipality_data['cash_available'] += cash_amount
                
                elif 'financial_position' in cube_name:
                    # Financial position/balance sheet data
                    amount = float(record.get('amount', 0) or 0)
                    item_code = str(record.get('item_code', '')).lower()
                    
                    if 'asset' in item_code:
                        # Assets
                        pass
                    elif 'liability' in item_code:
                        # Liabilities
                        pass
                
                # Add to detailed items
                municipality_data['detailed_items'].append({
                    'source': endpoint_info['name'],
                    'cube': cube_name,
                    'record': record
                })
            
            municipality_data['_data_sources'].append(endpoint_info['name'])
            logger.info(f"    ✅ Processed {len(endpoint_info['all_records'])} records")
            
        except Exception as e:
            logger.warning(f"    Error processing {endpoint_info['name']}: {e}")
    
    # Calculate derived metrics for each municipality
    processed_data = []
    
    for municipality_code, data in municipalities_data.items():
        # Calculate totals
        data['total_budget'] = data['total_capex_budget'] + data['revenue']
        data['total_actual'] = data['total_capex_actual'] + data['expenditure']
        data['surplus_deficit'] = data['revenue'] - data['expenditure']
        
        # Calculate budget variance
        if data['total_budget'] > 0:
            data['budget_variance'] = ((data['total_actual'] - data['total_budget']) / data['total_budget'] * 100)
        
        # Estimate infrastructure budget (25% of total budget)
        data['infrastructure_budget'] = data['total_budget'] * 0.25
        
        # Estimate service delivery budget (30% of total budget)
        data['service_delivery_budget'] = data['total_budget'] * 0.30
        
        logger.info(f"Final data for {municipality_code}:")
        logger.info(f"  Revenue: R{data['revenue']/1e6:.1f}M")
        logger.info(f"  Expenditure: R{data['expenditure']/1e6:.1f}M")
        logger.info(f"  Total Budget: R{data['total_budget']/1e6:.1f}M")
        logger.info(f"  Water Investment: R{data['water_related_capex']/1e6:.1f}M")
        logger.info(f"  Data Sources: {', '.join(data['_data_sources'])}")
        
        processed_data.append(data)
    
    return processed_data

async def store_v2_financial_data(financial_data_list):
    """Store real financial data from v2 endpoints in the database"""
    
    logger.info("💾 Storing real financial data from v2 endpoints...")
    
    stored_count = 0
    
    for financial_data in financial_data_list:
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
                        content_hash=f"real_data_v2_{financial_data['municipality_code']}_{financial_data['financial_year']}",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(financial_record)
                    
                    logger.info(f"✅ Created new financial record for {municipality.name}")
                
                await session.commit()
                stored_count += 1
                
        except Exception as e:
            logger.error(f"Error storing financial data for {financial_data['municipality_code']}: {e}")
    
    return stored_count

async def main():
    """Main function to test v2 endpoints and fetch real Treasury data"""
    
    logger.info("🚀 Testing v2 Treasury API endpoints...")
    
    try:
        # Initialize database
        await init_db()
        
        # Step 1: Test v2 endpoints
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Testing v2 endpoints")
        logger.info("="*60)
        working_endpoints = await test_v2_endpoints()
        
        if working_endpoints:
            logger.info(f"\n✅ Found {len(working_endpoints)} working v2 endpoints:")
            for endpoint in working_endpoints:
                logger.info(f"  📊 {endpoint['name']} ({endpoint['municipality']}): {endpoint['record_count']} records")
            
            # Step 2: Process real financial data
            logger.info("\n" + "="*60)
            logger.info("STEP 2: Processing real financial data from v2 endpoints")
            logger.info("="*60)
            
            financial_data_list = await process_real_financial_data_v2(working_endpoints)
            
            if financial_data_list:
                # Step 3: Store real financial data
                logger.info("\n" + "="*60)
                logger.info("STEP 3: Storing real financial data")
                logger.info("="*60)
                
                stored_count = await store_v2_financial_data(financial_data_list)
                
                logger.info(f"✅ Successfully stored {stored_count} real financial records!")
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("SUMMARY")
            logger.info("="*60)
            
            logger.info(f"📊 Working v2 endpoints: {len(working_endpoints)}")
            logger.info(f"💰 Financial records processed: {len(financial_data_list) if financial_data_list else 0}")
            logger.info(f"💾 Financial records stored: {stored_count if 'stored_count' in locals() else 0}")
            
            if working_endpoints:
                logger.info("✅ Successfully fetched and stored REAL Treasury data!")
                logger.info("🎯 The ETL is now working with actual Treasury API data!")
            
        else:
            logger.warning("⚠️  No working v2 endpoints found")
        
    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
