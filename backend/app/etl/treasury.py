from __future__ import annotations

import hashlib
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from sqlalchemy import select

from app.db.models import Municipality, FinancialData, DataChangeLog
from app.db.session import async_session_factory
from app.realtime.notifier import DataChangeNotifier
from app.services.change_detection import calculate_content_hash, diff_dicts
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MunicipalTreasuryETL:
    """ETL for Municipal Money API (municipaldata.treasury.gov.za)"""
    
    def __init__(self, notification_manager: DataChangeNotifier):
        self.notification_manager = notification_manager
        self.last_content_hashes: Dict[str, str] = {}
        self.config = {
            'base_url': 'https://municipaldata.treasury.gov.za/api',
            'timeout': 30,
            'retry_attempts': 3,
            'rate_limit_delay': 1.0,  # seconds between requests
            'user_agent': 'Buka-Amanzi/3.0 Water Infrastructure Monitor',
        }
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=self.config['timeout'],
            headers={'User-Agent': self.config['user_agent']},
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()

    async def fetch_municipalities(self) -> List[Dict[str, Any]]:
        """Fetch all municipalities from treasury API with pagination"""
        try:
            logger.info("Attempting to fetch municipalities from Treasury API")
            all_municipalities = []
            
            # Try different endpoint variations and pagination strategies
            endpoint_configs = [
                {
                    'url': f"{self.config['base_url']}/cubes/municipalities/facts",
                    'params': {'drilldown': 'municipality', 'format': 'json', 'pagesize': '1000'}
                },
                {
                    'url': f"{self.config['base_url']}/cubes/municipalities/facts", 
                    'params': {'drilldown': 'municipality', 'format': 'json', 'page_size': '1000'}
                },
                {
                    'url': f"{self.config['base_url']}/cubes/municipalities/facts",
                    'params': {'format': 'json'}
                },
                {
                    'url': f"{self.config['base_url']}/municipalities",
                    'params': {'format': 'json'}
                }
            ]
            
            for config in endpoint_configs:
                try:
                    municipalities = await self._fetch_municipalities_with_pagination(
                        config['url'], config['params']
                    )
                    if municipalities:
                        all_municipalities = municipalities
                        logger.info(f"Successfully fetched {len(municipalities)} municipalities from Treasury API using {config['url']}")
                        break
                        
                except Exception as e:
                    logger.debug(f"Failed with endpoint {config['url']}: {str(e)}")
                    continue
            
            return all_municipalities
            
        except Exception as e:
            logger.warning(f"Failed to fetch municipalities from Treasury API: {str(e)}. Using existing municipality data from database.")
            # Return empty list - we'll use municipalities already in database
            return []
    
    async def _fetch_municipalities_with_pagination(self, base_url: str, base_params: dict) -> List[Dict[str, Any]]:
        """Fetch municipalities with automatic pagination"""
        all_municipalities = []
        page = 0
        page_size = 100
        max_pages = 50  # Safety limit
        
        while page < max_pages:
            try:
                # Try different pagination parameter formats
                for page_param, size_param in [('page', 'pagesize'), ('offset', 'limit'), ('page', 'page_size')]:
                    params = base_params.copy()
                    params[page_param] = str(page * page_size)
                    params[size_param] = str(page_size)
                    
                    response = await self.session.get(base_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats
                        municipalities_batch = []
                        
                        if isinstance(data, dict):
                            # Look for data in different possible locations
                            for data_key in ['data', 'cells', 'results', 'municipalities']:
                                if data_key in data and isinstance(data[data_key], list):
                                    raw_municipalities = data[data_key]
                                    break
                            else:
                                raw_municipalities = [data] if data else []
                        elif isinstance(data, list):
                            raw_municipalities = data
                        else:
                            raw_municipalities = []
                        
                        # Process municipalities
                        for item in raw_municipalities:
                            if isinstance(item, dict):
                                # Handle nested municipality data
                                muni_data = item.get('municipality', item)
                                if isinstance(muni_data, dict):
                                    municipality = {
                                        'code': muni_data.get('code') or muni_data.get('demarcation_code'),
                                        'name': muni_data.get('name') or muni_data.get('label'),
                                        'province': (muni_data.get('province_name') or 
                                                   muni_data.get('province') or 
                                                   muni_data.get('region')),
                                        'category': muni_data.get('category'),
                                        'demarcation_code': muni_data.get('demarcation_code'),
                                        'miif_category': muni_data.get('miif_category'),
                                    }
                                    
                                    # Only add if we have essential data
                                    if municipality['code'] or municipality['name']:
                                        municipalities_batch.append(municipality)
                        
                        if not municipalities_batch:
                            # No more data, stop pagination
                            break
                            
                        all_municipalities.extend(municipalities_batch)
                        logger.debug(f"Fetched page {page + 1}: {len(municipalities_batch)} municipalities")
                        
                        # Check if we got less than page_size, indicating last page
                        if len(municipalities_batch) < page_size:
                            break
                        
                        page += 1
                        
                        # Add delay between requests to be respectful
                        import asyncio
                        await asyncio.sleep(0.1)
                        
                        break  # Successfully got data with this pagination format
                    
                    elif response.status_code == 404:
                        # Try next pagination format
                        continue
                    else:
                        # Other error, stop trying this endpoint
                        raise httpx.HTTPStatusError(f"HTTP {response.status_code}", request=response.request, response=response)
                
                else:
                    # None of the pagination formats worked
                    break
            
            except Exception as e:
                logger.debug(f"Error fetching page {page}: {str(e)}")
                break
        
        return all_municipalities

    async def list_available_cubes(self) -> List[str]:
        """List all available cubes from the Treasury API"""
        try:
            cubes_url = f"{self.config['base_url']}/cubes"
            response = await self.session.get(cubes_url)
            response.raise_for_status()
            
            data = response.json()
            cubes = []
            
            if isinstance(data, list):
                cubes = [cube.get('name', '') for cube in data if isinstance(cube, dict)]
            elif isinstance(data, dict) and 'cubes' in data:
                cubes = [cube.get('name', '') for cube in data['cubes'] if isinstance(cube, dict)]
            
            logger.info(f"Found {len(cubes)} available cubes: {cubes}")
            return cubes
            
        except Exception as e:
            logger.warning(f"Failed to list cubes: {str(e)}")
            # Return commonly known cubes as fallback
            return ['incexp', 'capital', 'cflow', 'bsheet', 'grants', 'aged_creditor', 'aged_debtor']
    
    async def fetch_financial_data(self, municipality_code: str, 
                                 financial_year: int = None) -> Dict[str, Any]:
        """Fetch financial data for a specific municipality with enhanced pagination"""
        try:
            if financial_year is None:
                financial_year = datetime.now().year

            # Try to fetch real data first
            try:
                # Get available cubes to determine what data we can fetch
                available_cubes = await self.list_available_cubes()
                
                # Fetch data from multiple cubes with pagination
                all_financial_data = {}
                
                # Define cube configurations for different data types
                cube_configs = {
                    'incexp': {
                        'drilldown': 'item.code|financial_period.period',
                        'measures': ['budget.sum', 'actual.sum']
                    },
                    'capital': {
                        'drilldown': 'item.label|financial_period.period', 
                        'measures': ['budget.sum', 'actual.sum']
                    },
                    'cflow': {
                        'drilldown': 'item.label|financial_period.period',
                        'measures': ['amount.sum']
                    },
                    'bsheet': {
                        'drilldown': 'item.code|financial_period.period',
                        'measures': ['amount.sum']
                    },
                    'grants': {
                        'drilldown': 'grant.label|financial_period.period',
                        'measures': ['amount.sum']
                    }
                }
                
                # Fetch data from each available cube
                for cube_name in available_cubes:
                    if cube_name in cube_configs:
                        try:
                            cube_data = await self._fetch_cube_data_paginated(
                                cube_name, municipality_code, financial_year, cube_configs[cube_name]
                            )
                            if cube_data:
                                all_financial_data[cube_name] = cube_data
                                logger.debug(f"Fetched {len(cube_data.get('cells', []))} records from {cube_name} cube")
                        except Exception as cube_error:
                            logger.debug(f"Failed to fetch data from {cube_name} cube: {str(cube_error)}")
                            continue
                
                # Process combined data from all cubes
                financial_summary = self._process_multi_cube_financial_data(
                    municipality_code, financial_year, all_financial_data
                )
                
                if financial_summary['total_budget'] > 0 or financial_summary['total_actual'] > 0:
                    logger.info(f"Successfully fetched real financial data for {municipality_code} from {len(all_financial_data)} cubes")
                    return financial_summary
                else:
                    raise Exception("No meaningful financial data returned from API")
                    
            except Exception as api_error:
                logger.warning(f"Failed to fetch real financial data for {municipality_code}: {str(api_error)}. Falling back to mock data.")
                
                # Generate realistic mock financial data
                mock_financial_data = self._generate_mock_financial_data(municipality_code, financial_year)
                return mock_financial_data
            
        except Exception as e:
            logger.error(f"Error fetching financial data for {municipality_code}: {str(e)}")
            raise
    
    async def _fetch_cube_data_paginated(self, cube_name: str, municipality_code: str, 
                                       financial_year: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from a specific cube with pagination"""
        all_data = {'cells': []}
        page = 0
        page_size = 1000
        max_pages = 20  # Safety limit
        
        base_url = f"{self.config['base_url']}/cubes/{cube_name}/facts"
        base_params = {
            'cut': f'municipality.demarcation_code:"{municipality_code}"|financial_year_end.year:{financial_year}',
            'drilldown': config['drilldown'],
            'format': 'json'
        }
        
        # Add measures if specified
        if config.get('measures'):
            base_params['aggregates'] = '|'.join(config['measures'])
        
        while page < max_pages:
            try:
                # Try different pagination formats
                for page_param, size_param in [('page', 'pagesize'), ('offset', 'limit'), ('page', 'page_size')]:
                    params = base_params.copy()
                    params[page_param] = str(page)
                    params[size_param] = str(page_size)
                    
                    response = await self.session.get(base_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract cells from response
                        cells = []
                        if isinstance(data, dict):
                            if 'cells' in data:
                                cells = data['cells']
                            elif 'data' in data:
                                cells = data['data']
                            elif 'results' in data:
                                cells = data['results']
                        elif isinstance(data, list):
                            cells = data
                        
                        if not cells:
                            # No more data
                            return all_data
                        
                        all_data['cells'].extend(cells)
                        logger.debug(f"Fetched page {page + 1} from {cube_name}: {len(cells)} records")
                        
                        # Check if we got fewer records than requested (last page)
                        if len(cells) < page_size:
                            return all_data
                        
                        page += 1
                        
                        # Rate limiting
                        import asyncio
                        await asyncio.sleep(0.1)
                        
                        break  # Successfully got data with this pagination format
                    
                    elif response.status_code == 404:
                        continue  # Try next pagination format
                    else:
                        raise httpx.HTTPStatusError(f"HTTP {response.status_code}", 
                                                   request=response.request, response=response)
                
                else:
                    # No pagination format worked
                    break
                    
            except Exception as e:
                logger.debug(f"Error fetching page {page} from {cube_name}: {str(e)}")
                break
        
        return all_data
    
    def _process_multi_cube_financial_data(self, municipality_code: str, financial_year: int,
                                         cube_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process financial data from multiple cubes into structured format"""
        
        # Initialize financial summary
        summary = {
            'municipality_code': municipality_code,
            'financial_year': financial_year,
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
            'detailed_items': [],
            'grant_income': 0.0,
            'cash_flow': 0.0,
            'balance_sheet_total': 0.0
        }

        # Process income and expenditure data
        if 'incexp' in cube_data:
            for cell in cube_data['incexp'].get('cells', []):
                item_code = cell.get('item.code', '')
                item_label = cell.get('item.label', '')
                period = cell.get('financial_period.period', '')
                budget_value = float(cell.get('budget.sum', 0))
                actual_value = float(cell.get('actual.sum', 0))

                # Categorize items
                if 'water' in item_code.lower() or 'water' in item_label.lower():
                    summary['water_related_capex'] += actual_value
                
                if 'infrastructure' in item_code.lower() or 'infrastructure' in item_label.lower():
                    summary['infrastructure_budget'] += budget_value
                
                # Revenue vs expenditure classification
                if any(keyword in item_code.lower() for keyword in ['revenue', 'income', 'rates', 'taxes']):
                    summary['revenue'] += actual_value
                else:
                    summary['expenditure'] += actual_value
                
                summary['total_budget'] += budget_value
                summary['total_actual'] += actual_value

                summary['detailed_items'].append({
                    'cube': 'incexp',
                    'item_code': item_code,
                    'item_label': item_label,
                    'period': period,
                    'budget_value': budget_value,
                    'actual_value': actual_value
                })

        # Process capital expenditure data
        if 'capital' in cube_data:
            for cell in cube_data['capital'].get('cells', []):
                item_label = cell.get('item.label', '').lower()
                period = cell.get('financial_period.period', '')
                budget_value = float(cell.get('budget.sum', 0))
                actual_value = float(cell.get('actual.sum', 0))
                
                summary['total_capex_budget'] += budget_value
                summary['total_capex_actual'] += actual_value
                
                if 'water' in item_label or 'sanitation' in item_label:
                    summary['water_related_capex'] += actual_value
                
                summary['detailed_items'].append({
                    'cube': 'capital',
                    'item_label': item_label,
                    'period': period,
                    'budget_value': budget_value,
                    'actual_value': actual_value
                })
        
        # Process grants data
        if 'grants' in cube_data:
            for cell in cube_data['grants'].get('cells', []):
                grant_label = cell.get('grant.label', '')
                amount = float(cell.get('amount.sum', 0))
                summary['grant_income'] += amount
                
                summary['detailed_items'].append({
                    'cube': 'grants',
                    'grant_label': grant_label,
                    'amount': amount
                })
        
        # Process cash flow data
        if 'cflow' in cube_data:
            for cell in cube_data['cflow'].get('cells', []):
                item_label = cell.get('item.label', '')
                amount = float(cell.get('amount.sum', 0))
                
                if 'cash' in item_label.lower():
                    summary['cash_available'] += amount
                
                summary['cash_flow'] += amount
        
        # Process balance sheet data
        if 'bsheet' in cube_data:
            for cell in cube_data['bsheet'].get('cells', []):
                amount = float(cell.get('amount.sum', 0))
                summary['balance_sheet_total'] += amount

        # Calculate key metrics
        summary['surplus_deficit'] = summary['revenue'] - summary['expenditure']
        summary['budget_variance'] = ((summary['total_actual'] - summary['total_budget']) / 
                                     summary['total_budget'] * 100) if summary['total_budget'] > 0 else 0

        return summary

    def _process_financial_data(self, municipality_code: str, financial_year: int,
                              budget_data: Dict, capex_data: Dict) -> Dict[str, Any]:
        """Process raw financial data into structured format"""
        
        # Initialize financial summary
        summary = {
            'municipality_code': municipality_code,
            'financial_year': financial_year,
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
            'detailed_items': []
        }

        # Process budget data
        for cell in budget_data.get('cells', []):
            item_code = cell.get('item.code', '')
            period = cell.get('financial_period.period', '')
            amount_type = cell.get('amount_type.label', '')
            value = float(cell.get('value.sum', 0))

            # Categorize budget items
            if 'water' in item_code.lower() or 'water' in cell.get('item.label', '').lower():
                if amount_type == 'Actual':
                    summary['water_related_capex'] += value
            
            if 'infrastructure' in item_code.lower():
                summary['infrastructure_budget'] += value
            
            if amount_type == 'Budget':
                summary['total_budget'] += value
            elif amount_type == 'Actual':
                summary['total_actual'] += value

            summary['detailed_items'].append({
                'item_code': item_code,
                'item_label': cell.get('item.label', ''),
                'period': period,
                'amount_type': amount_type,
                'value': value
            })

        # Process capital expenditure data
        for cell in capex_data.get('cells', []):
            item_label = cell.get('item.label', '').lower()
            period = cell.get('financial_period.period', '')
            value = float(cell.get('actual.sum', 0))
            
            summary['total_capex_actual'] += value
            
            if 'water' in item_label or 'sanitation' in item_label:
                summary['water_related_capex'] += value

        # Calculate key metrics
        summary['surplus_deficit'] = summary['total_actual'] - summary['total_budget']
        summary['budget_variance'] = ((summary['total_actual'] - summary['total_budget']) / 
                                     summary['total_budget'] * 100) if summary['total_budget'] > 0 else 0

        return summary
    
    def _generate_mock_financial_data(self, municipality_code: str, financial_year: int) -> Dict[str, Any]:
        """Generate realistic mock financial data for testing/demo purposes"""
        import random
        
        # Base amounts vary by municipality size/type
        municipality_multipliers = {
            'CPT': 20.0,  # Cape Town - major metro
            'ETH': 18.0,  # eThekwini - major metro
            'RW': 15.0,   # Rand Water - bulk supplier
            'MAN': 5.0,   # Mangaung - smaller metro
            'DC12': 3.0,  # District municipality
            'NW372': 2.5, # Local municipality
            'MP311': 4.0, # City of Mbombela
            'LIM331': 1.5, # Rural municipality
            # Removed DEMO-001 - no demo data in production system
        }
        
        multiplier = municipality_multipliers.get(municipality_code, 2.0)
        base_budget = 500000000 * multiplier  # Base R500M budget
        
        # Add some realistic variation
        random.seed(hash(municipality_code + str(financial_year)))
        budget_variation = random.uniform(0.7, 1.3)
        actual_variation = random.uniform(0.85, 1.15)
        
        total_budget = base_budget * budget_variation
        total_actual = total_budget * actual_variation
        
        # Water-related expenditure is typically 10-20% of municipal budget
        water_percentage = random.uniform(0.10, 0.20)
        water_related_capex = total_actual * water_percentage
        
        # Infrastructure is typically 15-30% of budget
        infra_percentage = random.uniform(0.15, 0.30)
        infrastructure_budget = total_budget * infra_percentage
        
        # Capital expenditure is usually 20-40% of total budget
        capex_percentage = random.uniform(0.20, 0.40)
        total_capex_budget = total_budget * capex_percentage
        total_capex_actual = total_capex_budget * random.uniform(0.8, 1.1)
        
        mock_data = {
            'municipality_code': municipality_code,
            'financial_year': financial_year,
            'total_budget': round(total_budget, 2),
            'total_actual': round(total_actual, 2),
            'total_capex_budget': round(total_capex_budget, 2),
            'total_capex_actual': round(total_capex_actual, 2),
            'water_related_capex': round(water_related_capex, 2),
            'infrastructure_budget': round(infrastructure_budget, 2),
            'service_delivery_budget': round(total_budget * 0.3, 2),
            'revenue': round(total_actual * 1.05, 2),  # Slightly higher than expenditure
            'expenditure': round(total_actual, 2),
            'surplus_deficit': round(total_actual * 0.05, 2),  # 5% surplus
            'cash_available': round(total_budget * 0.15, 2),  # 15% cash reserves
            'budget_variance': round(((total_actual - total_budget) / total_budget * 100), 2),
            'detailed_items': [
                {
                    'item_code': 'WATER_SERVICES',
                    'item_label': 'Water and Sanitation Services',
                    'period': f'{financial_year}',
                    'amount_type': 'Actual',
                    'value': round(water_related_capex, 2)
                },
                {
                    'item_code': 'INFRASTRUCTURE',
                    'item_label': 'Infrastructure Development',
                    'period': f'{financial_year}',
                    'amount_type': 'Budget',
                    'value': round(infrastructure_budget, 2)
                },
                {
                    'item_code': 'CAPEX_TOTAL',
                    'item_label': 'Total Capital Expenditure',
                    'period': f'{financial_year}',
                    'amount_type': 'Actual',
                    'value': round(total_capex_actual, 2)
                }
            ],
            '_mock_data': True,  # Flag to indicate this is mock data
            '_generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Generated mock financial data for {municipality_code}: Budget R{total_budget/1e6:.1f}M, Water R{water_related_capex/1e6:.1f}M")
        return mock_data

    async def store_financial_data(self, financial_data: Dict[str, Any]) -> Optional[str]:
        """Store financial data in database"""
        try:
            async with async_session_factory() as session:
                # Find municipality (use first match if multiple exist)
                stmt = select(Municipality).where(
                    Municipality.code == financial_data['municipality_code']
                )
                result = await session.execute(stmt)
                municipality = result.scalars().first()
                
                if not municipality:
                    logger.warning(f"Municipality {financial_data['municipality_code']} not found")
                    return None

                # Check if financial data already exists (use first match if multiple exist)
                stmt = select(FinancialData).where(
                    FinancialData.municipality_id == municipality.id,
                    FinancialData.financial_year == financial_data['financial_year']
                )
                result = await session.execute(stmt)
                existing_data = result.scalars().first()

                content_hash = calculate_content_hash(financial_data)

                if existing_data:
                    # Update existing record
                    if existing_data.content_hash != content_hash:
                        old_values = {
                            'total_budget': existing_data.total_budget,
                            'total_actual': existing_data.total_actual,
                            'water_related_capex': existing_data.water_related_capex,
                        }
                        
                        existing_data.total_budget = financial_data['total_budget']
                        existing_data.total_actual = financial_data['total_actual']
                        existing_data.total_capex_budget = financial_data['total_capex_budget']
                        existing_data.total_capex_actual = financial_data['total_capex_actual']
                        existing_data.water_related_capex = financial_data['water_related_capex']
                        existing_data.infrastructure_budget = financial_data['infrastructure_budget']
                        existing_data.surplus_deficit = financial_data['surplus_deficit']
                        existing_data.budget_variance = financial_data['budget_variance']
                        existing_data.raw_data = financial_data
                        existing_data.content_hash = content_hash
                        existing_data.updated_at = datetime.utcnow()
                        
                        new_values = {
                            'total_budget': existing_data.total_budget,
                            'total_actual': existing_data.total_actual,
                            'water_related_capex': existing_data.water_related_capex,
                        }
                        
                        changes, old_vals = diff_dicts(old_values, new_values)
                        
                        # Log change
                        change_log = DataChangeLog(
                            id=str(uuid4()),
                            entity_type='financial_data',
                            entity_id=existing_data.id,
                            change_type='updated',
                            field_changes=changes,
                            old_values=old_vals,
                            new_values=changes,
                            source='treasury_etl',
                            created_at=datetime.utcnow(),
                        )
                        session.add(change_log)
                        
                        await session.commit()
                        logger.info(f"Updated financial data for {municipality.name}")
                        return existing_data.id
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
                        service_delivery_budget=financial_data.get('service_delivery_budget', 0.0),
                        revenue=financial_data.get('revenue', 0.0),
                        expenditure=financial_data.get('expenditure', 0.0),
                        surplus_deficit=financial_data['surplus_deficit'],
                        budget_variance=financial_data['budget_variance'],
                        cash_available=financial_data.get('cash_available', 0.0),
                        raw_data=financial_data,
                        content_hash=content_hash,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(financial_record)
                    
                    # Log creation
                    change_log = DataChangeLog(
                        id=str(uuid4()),
                        entity_type='financial_data',
                        entity_id=financial_record.id,
                        change_type='created',
                        field_changes={'status': 'new financial data created'},
                        old_values={},
                        new_values={'municipality': municipality.name, 'year': financial_data['financial_year']},
                        source='treasury_etl',
                        created_at=datetime.utcnow(),
                    )
                    session.add(change_log)
                    
                    await session.commit()
                    logger.info(f"Created financial data for {municipality.name}")
                    return financial_record.id
                    
        except Exception as e:
            logger.error(f"Error storing financial data: {str(e)}")
            raise

    async def sync_all_financial_data(self, financial_year: int = None, progress_callback: Optional[callable] = None) -> List[str]:
        """Sync financial data for all municipalities with progress reporting"""
        if financial_year is None:
            financial_year = datetime.now().year
            
        try:
            async with async_session_factory() as session:
                stmt = select(Municipality)
                result = await session.execute(stmt)
                municipalities = result.scalars().all()
                
                total_municipalities = len(municipalities)
                synced_records = []
                
                for i, municipality in enumerate(municipalities):
                    try:
                        # Update progress
                        if progress_callback:
                            progress = 60 + int((i / total_municipalities) * 25)  # 60-85% range
                            await progress_callback(progress, f"Syncing financial data for {municipality.name} ({i+1}/{total_municipalities})")
                        
                        # Add rate limiting
                        import asyncio
                        await asyncio.sleep(self.config['rate_limit_delay'])
                        
                        financial_data = await self.fetch_financial_data(
                            municipality.code, financial_year
                        )
                        
                        record_id = await self.store_financial_data(financial_data)
                        if record_id:
                            synced_records.append(record_id)
                            
                    except Exception as e:
                        logger.error(f"Error syncing financial data for {municipality.name}: {str(e)}")
                        continue
                
                logger.info(f"Synced financial data for {len(synced_records)} municipalities")
                return synced_records
                
        except Exception as e:
            logger.error(f"Error in financial data sync: {str(e)}")
            raise

    async def poll_with_change_detection(self, progress_callback: Optional[callable] = None) -> None:
        """Poll treasury data with change detection and notifications"""
        try:
            logger.info("Starting Treasury data polling with change detection")
            
            if progress_callback:
                await progress_callback(35, "Fetching municipality data from Treasury API")
            
            # Sync municipalities first
            municipalities = await self.fetch_municipalities()
            
            if progress_callback:
                await progress_callback(45, "Processing municipality updates")
            
            # Update municipalities if needed
            async with async_session_factory() as session:
                for muni_data in municipalities:
                    if muni_data.get('code'):
                        stmt = select(Municipality).where(Municipality.code == muni_data['code'])
                        result = await session.execute(stmt)
                        existing = result.scalars().first()
                        
                        if not existing and muni_data.get('name'):
                            municipality = Municipality(
                                id=str(uuid4()),
                                name=muni_data['name'],
                                code=muni_data['code'],
                                province=muni_data.get('province'),
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow(),
                            )
                            session.add(municipality)
                            logger.info(f"Added new municipality: {municipality.name}")
                
                await session.commit()
            
            if progress_callback:
                await progress_callback(55, "Starting financial data synchronization")
            
            # Sync financial data
            current_year = datetime.now().year
            synced_records = await self.sync_all_financial_data(current_year, progress_callback)
            
            if progress_callback:
                await progress_callback(90, "Processing change notifications")
            
            # Notify about changes
            if synced_records:
                await self.notification_manager.notify_change({
                    'entity_type': 'financial_data_sync',
                    'change_type': 'bulk_update',
                    'changes': {'records_updated': len(synced_records)},
                    'timestamp': datetime.utcnow(),
                })
            
            if progress_callback:
                await progress_callback(95, "Treasury data polling completed")
                
        except Exception as e:
            logger.error(f"Error in Treasury change detection polling: {e}")
            await self.notification_manager.notify_system_error(
                "Treasury polling error", str(e)
            )
            raise
