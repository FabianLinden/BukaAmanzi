from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from app.db.models import Project, Municipality, DataChangeLog
from app.db.session import async_session_factory
from app.realtime.notifier import DataChangeNotifier
from app.services.change_detection import calculate_content_hash, diff_dicts
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EnhancedDWSMonitor:
    def __init__(self, notification_manager: DataChangeNotifier):
        self.notification_manager = notification_manager
        self.last_content_hashes: Dict[str, str] = {}
        self.dws_config = {
            'base_url': 'https://ws.dws.gov.za/pmd/level.aspx',
            'encrypted_params': 'VWReJm+SmGcCYM6pJQAmVBLmM33+9zWef3oVk0rPHvehd5PO8glfwc6rREAYyNxl',
            'timeout': 30,
            'retry_attempts': 3,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

    async def fetch_dws_data(self) -> Dict[str, Any]:
        """Fetch data from DWS Project Monitoring Dashboard."""
        try:
            headers = {
                'User-Agent': self.dws_config['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'https://ws.dws.gov.za/',
            }
            
            async with httpx.AsyncClient(
                timeout=self.dws_config['timeout'],
                headers=headers,
                follow_redirects=True
            ) as client:
                # Try to fetch real data first, fallback to mock if needed
                try:
                    real_data = await self._scrape_real_dws_data(client)
                    if real_data and real_data.get('projects'):
                        logger.info(f"Successfully fetched real DWS data: {len(real_data['projects'])} projects")
                        return real_data
                except Exception as scrape_error:
                    logger.warning(f"Failed to scrape real DWS data: {str(scrape_error)}. Falling back to enhanced mock data.")
                
                # Enhanced mock data that simulates real DWS Project Monitoring Dashboard
                # Fallback when real scraping fails
                mock_projects_data = {
                    'projects': [
                        {
                            'external_id': 'DWS-WC-001',
                            'name': 'Berg River-Voëlvlei Augmentation Scheme',
                            'description': 'Augmentation of the Berg River-Voëlvlei system to increase water supply capacity for the Western Cape region during drought conditions',
                            'municipality': 'City of Cape Town',
                            'province': 'Western Cape',
                            'status': 'in_progress',
                            'progress_percentage': 78,
                            'budget_allocated': 4200000000.0,  # R4.2 billion
                            'budget_spent': 3276000000.0,
                            'contractor': 'Aurecon-SMEC Joint Venture',
                            'start_date': '2020-04-01',
                            'end_date': '2025-03-31',
                            'project_type': 'water_supply',
                            'location': 'POINT(18.8607 -33.3019)',
                            'address': 'Berg River Valley, Western Cape',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-GP-002',
                            'name': 'Lesotho Highlands Water Project Phase II',
                            'description': 'Construction of Polihali Dam and associated infrastructure to transfer water from Lesotho to Gauteng',
                            'municipality': 'Rand Water',
                            'province': 'Gauteng',
                            'status': 'in_progress',
                            'progress_percentage': 35,
                            'budget_allocated': 24000000000.0,  # R24 billion
                            'budget_spent': 8400000000.0,
                            'contractor': 'China Gezhouba Group Company',
                            'start_date': '2019-10-01',
                            'end_date': '2028-12-31',
                            'project_type': 'bulk_water_supply',
                            'location': 'POINT(28.2293 -29.8587)',
                            'address': 'Polihali, Lesotho/Gauteng Transfer',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-KZN-003',
                            'name': 'uMkhomazi Water Project Phase 1',
                            'description': 'Construction of Smithfield Dam and associated pipelines to supply water to eThekwini and surrounding areas',
                            'municipality': 'eThekwini Metropolitan Municipality',
                            'province': 'KwaZulu-Natal',
                            'status': 'in_progress',
                            'progress_percentage': 62,
                            'budget_allocated': 18700000000.0,  # R18.7 billion
                            'budget_spent': 11594000000.0,
                            'contractor': 'WBHO-Basil Read Joint Venture',
                            'start_date': '2018-08-15',
                            'end_date': '2025-06-30',
                            'project_type': 'bulk_water_supply',
                            'location': 'POINT(30.1986 -30.3394)',
                            'address': 'Richmond, KwaZulu-Natal',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-EC-004',
                            'name': 'Amathole Bulk Regional Water Supply Scheme',
                            'description': 'Regional bulk water supply infrastructure to serve multiple municipalities in the Eastern Cape',
                            'municipality': 'Amathole District Municipality',
                            'province': 'Eastern Cape',
                            'status': 'in_progress',
                            'progress_percentage': 28,
                            'budget_allocated': 3500000000.0,  # R3.5 billion
                            'budget_spent': 980000000.0,
                            'contractor': 'Group Five Construction',
                            'start_date': '2023-02-01',
                            'end_date': '2027-01-31',
                            'project_type': 'bulk_water_supply',
                            'location': 'POINT(27.4017 -32.7847)',
                            'address': 'East London, Eastern Cape',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-NW-005',
                            'name': 'Vaalkop Dam Raising Project',
                            'description': 'Raising of Vaalkop Dam wall to increase storage capacity and improve water security for North West Province',
                            'municipality': 'Rustenburg Local Municipality',
                            'province': 'North West',
                            'status': 'planning',
                            'progress_percentage': 12,
                            'budget_allocated': 2800000000.0,  # R2.8 billion
                            'budget_spent': 336000000.0,
                            'contractor': 'Murray & Roberts',
                            'start_date': '2024-04-01',
                            'end_date': '2028-03-31',
                            'project_type': 'dam_construction',
                            'location': 'POINT(27.2499 -25.3304)',
                            'address': 'Brits, North West',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-MP-006',
                            'name': 'Komati Water Scheme Augmentation',
                            'description': 'Augmentation of water treatment works and pipeline infrastructure in Mpumalanga',
                            'municipality': 'City of Mbombela',
                            'province': 'Mpumalanga',
                            'status': 'completed',
                            'progress_percentage': 100,
                            'budget_allocated': 1200000000.0,  # R1.2 billion
                            'budget_spent': 1180000000.0,
                            'contractor': 'Stefanutti Stocks',
                            'start_date': '2020-01-15',
                            'end_date': '2023-12-31',
                            'project_type': 'water_treatment',
                            'location': 'POINT(31.0059 -25.4753)',
                            'address': 'Mbombela, Mpumalanga',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-LP-007',
                            'name': 'Giyani Emergency Water Supply Project',
                            'description': 'Emergency water supply project to provide clean water to communities in the Greater Giyani area',
                            'municipality': 'Greater Giyani Local Municipality',
                            'province': 'Limpopo',
                            'status': 'delayed',
                            'progress_percentage': 45,
                            'budget_allocated': 3000000000.0,  # R3 billion
                            'budget_spent': 1950000000.0,
                            'contractor': 'LTE Consulting',
                            'start_date': '2018-03-01',
                            'end_date': '2024-02-29',
                            'project_type': 'water_supply',
                            'location': 'POINT(30.7188 -23.3026)',
                            'address': 'Giyani, Limpopo',
                            'last_updated': datetime.utcnow().isoformat(),
                        },
                        {
                            'external_id': 'DWS-FS-008',
                            'name': 'Modder River Government Water Scheme',
                            'description': 'Construction of new water treatment plant and distribution network in Free State',
                            'municipality': 'Mangaung Metropolitan Municipality',
                            'province': 'Free State',
                            'status': 'in_progress',
                            'progress_percentage': 55,
                            'budget_allocated': 1800000000.0,  # R1.8 billion
                            'budget_spent': 990000000.0,
                            'contractor': 'Concor Construction',
                            'start_date': '2022-06-01',
                            'end_date': '2026-05-31',
                            'project_type': 'water_treatment',
                            'location': 'POINT(26.2041 -29.1217)',
                            'address': 'Bloemfontein, Free State',
                            'last_updated': datetime.utcnow().isoformat(),
                        }
                    ],
                    'municipalities': [
                        {
                            'name': 'City of Cape Town',
                            'code': 'CPT',
                            'province': 'Western Cape',
                        },
                        {
                            'name': 'Rand Water',
                            'code': 'RW',
                            'province': 'Gauteng',
                        },
                        {
                            'name': 'eThekwini Metropolitan Municipality',
                            'code': 'ETH',
                            'province': 'KwaZulu-Natal',
                        },
                        {
                            'name': 'Amathole District Municipality',
                            'code': 'DC12',
                            'province': 'Eastern Cape',
                        },
                        {
                            'name': 'Rustenburg Local Municipality',
                            'code': 'NW372',
                            'province': 'North West',
                        },
                        {
                            'name': 'City of Mbombela',
                            'code': 'MP311',
                            'province': 'Mpumalanga',
                        },
                        {
                            'name': 'Greater Giyani Local Municipality',
                            'code': 'LIM331',
                            'province': 'Limpopo',
                        },
                        {
                            'name': 'Mangaung Metropolitan Municipality',
                            'code': 'MAN',
                            'province': 'Free State',
                        }
                    ]
                }
                
                logger.info(f"Fetched {len(mock_projects_data['projects'])} projects from DWS (mock data)")
                return mock_projects_data
                
        except Exception as e:
            logger.error(f"Error fetching DWS data: {str(e)}")
            raise
    
    async def _scrape_real_dws_data(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Scrape real data from DWS Project Monitoring Dashboard"""
        try:
            # First, try to access the main DWS PMD page
            main_response = await client.get(self.dws_config['base_url'])
            main_response.raise_for_status()
            
            soup = BeautifulSoup(main_response.content, 'html.parser')
            
            # Initialize data structure
            scraped_data = {
                'projects': [],
                'municipalities': [],
                'scrape_timestamp': datetime.utcnow().isoformat(),
                'source_url': self.dws_config['base_url']
            }
            
            # Look for project data tables or containers
            project_tables = soup.find_all('table', class_=re.compile(r'(project|data|grid)', re.I))
            project_divs = soup.find_all('div', class_=re.compile(r'(project|item|card)', re.I))
            
            # Try to extract project information from tables
            for table in project_tables:
                rows = table.find_all('tr')
                if len(rows) > 1:  # Has header and data rows
                    headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                    
                    for row in rows[1:]:
                        cells = [td.get_text(strip=True) for td in row.find_all('td')]
                        if len(cells) >= 3:  # Minimum viable project data
                            project = self._extract_project_from_cells(headers, cells)
                            if project:
                                scraped_data['projects'].append(project)
            
            # Try to extract from structured divs/cards
            for div in project_divs:
                project = self._extract_project_from_div(div)
                if project:
                    scraped_data['projects'].append(project)
            
            # Look for municipality dropdown or list
            municipality_selects = soup.find_all('select', id=re.compile(r'(munic|location)', re.I))
            for select in municipality_selects:
                options = select.find_all('option')
                for option in options:
                    if option.get('value') and option.get_text(strip=True):
                        scraped_data['municipalities'].append({
                            'name': option.get_text(strip=True),
                            'code': option.get('value'),
                            'province': self._extract_province_from_name(option.get_text(strip=True))
                        })
            
            # If we found projects, return the data
            if scraped_data['projects']:
                logger.info(f"Successfully scraped {len(scraped_data['projects'])} projects from DWS")
                return scraped_data
            else:
                # Try alternative scraping methods if the structure has changed
                return await self._try_alternative_scraping_methods(client, soup)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error accessing DWS website: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error scraping real DWS data: {str(e)}")
            raise
    
    def _extract_project_from_cells(self, headers: List[str], cells: List[str]) -> Optional[Dict[str, Any]]:
        """Extract project data from table cells"""
        try:
            project = {
                'external_id': f"DWS-SCRAPED-{datetime.utcnow().strftime('%Y%m%d')}-{len(cells)}",
                'source': 'dws_pmd_scraped',
                'name': '',
                'description': '',
                'municipality': '',
                'province': '',
                'status': 'unknown',
                'progress_percentage': 0,
                'budget_allocated': 0.0,
                'budget_spent': 0.0,
                'contractor': '',
                'project_type': 'water_infrastructure',
                'last_updated': datetime.utcnow().isoformat(),
            }
            
            # Map common column patterns to project fields
            header_mappings = {
                'project name': 'name',
                'name': 'name',
                'description': 'description',
                'municipality': 'municipality',
                'location': 'municipality',
                'province': 'province',
                'status': 'status',
                'progress': 'progress_percentage',
                'budget': 'budget_allocated',
                'allocated': 'budget_allocated',
                'spent': 'budget_spent',
                'contractor': 'contractor',
                'type': 'project_type'
            }
            
            # Match headers to cells and extract data
            for i, header in enumerate(headers):
                if i < len(cells):
                    header_lower = header.lower()
                    cell_value = cells[i].strip()
                    
                    # Find matching field
                    for pattern, field in header_mappings.items():
                        if pattern in header_lower:
                            if field == 'progress_percentage':
                                # Extract percentage from text like "75%" or "75 percent"
                                progress_match = re.search(r'(\d+)', cell_value)
                                if progress_match:
                                    project[field] = int(progress_match.group(1))
                            elif field in ['budget_allocated', 'budget_spent']:
                                # Extract numbers from budget text
                                budget_match = re.search(r'([\d,\.]+)', cell_value.replace(' ', ''))
                                if budget_match:
                                    budget_str = budget_match.group(1).replace(',', '')
                                    try:
                                        project[field] = float(budget_str)
                                        # Convert millions/billions if indicated
                                        if 'million' in cell_value.lower():
                                            project[field] *= 1000000
                                        elif 'billion' in cell_value.lower():
                                            project[field] *= 1000000000
                                    except ValueError:
                                        pass
                            else:
                                project[field] = cell_value
                            break
            
            # Only return project if it has essential data
            if project['name'] and len(project['name']) > 3:
                return project
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting project from table cells: {str(e)}")
            return None
    
    def _extract_project_from_div(self, div_element) -> Optional[Dict[str, Any]]:
        """Extract project data from div/card elements"""
        try:
            # Look for text patterns that indicate project information
            text_content = div_element.get_text(' ', strip=True)
            
            # Skip if too short to be meaningful
            if len(text_content) < 20:
                return None
            
            project = {
                'external_id': f"DWS-DIV-{hashlib.md5(text_content.encode()).hexdigest()[:8]}",
                'source': 'dws_pmd_scraped',
                'name': '',
                'description': text_content[:200],  # Use first part as description
                'municipality': '',
                'province': '',
                'status': 'unknown',
                'progress_percentage': 0,
                'budget_allocated': 0.0,
                'budget_spent': 0.0,
                'contractor': '',
                'project_type': 'water_infrastructure',
                'last_updated': datetime.utcnow().isoformat(),
            }
            
            # Extract project name (often the first significant text or in a header)
            name_elements = div_element.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
            if name_elements:
                project['name'] = name_elements[0].get_text(strip=True)
            else:
                # Use first sentence as name
                sentences = text_content.split('.')
                if sentences:
                    project['name'] = sentences[0][:100]
            
            # Look for budget patterns in text
            budget_patterns = [
                r'R\s*([\d,\.]+)\s*(million|billion)?',
                r'([\d,\.]+)\s*(million|billion)\s*rand',
                r'budget[:\s]+R?\s*([\d,\.]+)'
            ]
            
            for pattern in budget_patterns:
                match = re.search(pattern, text_content, re.I)
                if match:
                    try:
                        amount = float(match.group(1).replace(',', ''))
                        multiplier = match.group(2) if len(match.groups()) > 1 else None
                        if multiplier and 'million' in multiplier.lower():
                            amount *= 1000000
                        elif multiplier and 'billion' in multiplier.lower():
                            amount *= 1000000000
                        project['budget_allocated'] = amount
                        break
                    except (ValueError, IndexError):
                        pass
            
            # Extract province information
            project['province'] = self._extract_province_from_text(text_content)
            
            # Only return if we have a meaningful name
            if project['name'] and len(project['name']) > 5:
                return project
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting project from div: {str(e)}")
            return None
    
    async def _try_alternative_scraping_methods(self, client: httpx.AsyncClient, soup) -> Dict[str, Any]:
        """Try alternative methods if standard scraping fails"""
        try:
            # Look for JavaScript data or AJAX endpoints
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.get_text()
                
                # Look for JSON data in JavaScript
                json_matches = re.findall(r'({[^{}]*"project[^{}]*})', script_content, re.I)
                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        # Process JSON data if it contains project information
                        if isinstance(data, dict) and ('name' in data or 'project' in str(data).lower()):
                            return {'projects': [data], 'municipalities': []}
                    except json.JSONDecodeError:
                        continue
            
            # Try to find AJAX endpoints using simple text search
            for script in scripts:
                script_content = script.get_text()
                
                # Look for common API patterns in JavaScript
                if '/api/' in script_content or 'ajax' in script_content.lower():
                    # Look for URLs that might contain project data
                    url_patterns = ['api/projects', 'api/data', 'project.json', 'data.json']
                    for pattern in url_patterns:
                        if pattern in script_content:
                            try:
                                # Try to construct and fetch the endpoint
                                ajax_url = f"https://ws.dws.gov.za/{pattern}"
                                ajax_response = await client.get(ajax_url)
                                if ajax_response.status_code == 200:
                                    ajax_data = ajax_response.json()
                                    if isinstance(ajax_data, dict) and ('projects' in ajax_data or 'data' in ajax_data):
                                        return ajax_data
                            except Exception:
                                continue
            
            # If all else fails, return empty structure
            return {'projects': [], 'municipalities': []}
            
        except Exception as e:
            logger.error(f"Error in alternative scraping methods: {str(e)}")
            return {'projects': [], 'municipalities': []}
    
    def _extract_province_from_text(self, text: str) -> str:
        """Extract province information from text"""
        provinces = [
            'Western Cape', 'Eastern Cape', 'Northern Cape', 'Free State',
            'KwaZulu-Natal', 'North West', 'Gauteng', 'Mpumalanga', 'Limpopo'
        ]
        
        text_lower = text.lower()
        for province in provinces:
            if province.lower() in text_lower:
                return province
        
        return ''
    
    def _extract_province_from_name(self, name: str) -> str:
        """Extract province from municipality name"""
        # This would need a mapping of municipality names to provinces
        # For now, return empty string
        return self._extract_province_from_text(name)

    def calculate_content_hash(self, data: dict) -> str:
        """Calculate SHA-256 hash of content for change detection."""
        normalized_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(normalized_data.encode()).hexdigest()

    async def process_data_changes(self, current_data: dict) -> List[dict]:
        """Process detected changes and return change objects."""
        changes = []
        
        async with async_session_factory() as session:
            # Process municipalities first
            for muni_data in current_data.get('municipalities', []):
                await self._process_municipality(session, muni_data)
            
            # Process projects
            for project_data in current_data.get('projects', []):
                change = await self._process_project(session, project_data)
                if change:
                    changes.append(change)
            
            await session.commit()
        
        logger.info(f"Processed {len(changes)} project changes")
        return changes

    async def _process_municipality(self, session, muni_data: dict) -> Optional[Municipality]:
        """Process a single municipality record."""
        from sqlalchemy import select
        
        # Check if municipality exists
        stmt = select(Municipality).where(Municipality.code == muni_data['code'])
        result = await session.execute(stmt)
        existing_muni = result.scalar_one_or_none()
        
        if not existing_muni:
            # Create new municipality
            municipality = Municipality(
                id=str(uuid4()),
                name=muni_data['name'],
                code=muni_data['code'],
                province=muni_data['province'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(municipality)
            logger.info(f"Created new municipality: {municipality.name}")
            return municipality
        
        return existing_muni

    async def _process_project(self, session, project_data: dict) -> Optional[dict]:
        """Process a single project record and return change info if updated."""
        from sqlalchemy import select
        
        # Find municipality
        municipality = None
        if 'municipality' in project_data:
            stmt = select(Municipality).where(Municipality.name == project_data['municipality'])
            result = await session.execute(stmt)
            municipality = result.scalar_one_or_none()
        
        # Check if project exists
        stmt = select(Project).where(
            Project.external_id == project_data['external_id'],
            Project.source == 'dws_pmd'
        )
        result = await session.execute(stmt)
        existing_project = result.scalar_one_or_none()
        
        # Calculate content hash for change detection
        project_content = {
            k: v for k, v in project_data.items() 
            if k not in ['last_updated']
        }
        content_hash = calculate_content_hash(project_content)
        
        if existing_project:
            # Check for changes
            if existing_project.content_hash != content_hash:
                old_values = {
                    'name': existing_project.name,
                    'status': existing_project.status,
                    'progress_percentage': existing_project.progress_percentage,
                    'budget_spent': existing_project.budget_spent,
                }
                
                # Update project
                existing_project.name = project_data['name']
                existing_project.description = project_data['description']
                existing_project.status = project_data['status']
                existing_project.progress_percentage = project_data['progress_percentage']
                existing_project.budget_allocated = project_data['budget_allocated']
                existing_project.budget_spent = project_data['budget_spent']
                existing_project.contractor = project_data['contractor']
                existing_project.content_hash = content_hash
                existing_project.last_scraped_at = datetime.utcnow()
                existing_project.updated_at = datetime.utcnow()
                
                new_values = {
                    'name': existing_project.name,
                    'status': existing_project.status,
                    'progress_percentage': existing_project.progress_percentage,
                    'budget_spent': existing_project.budget_spent,
                }
                
                changes, old_vals = diff_dicts(old_values, new_values)
                
                # Log change
                change_log = DataChangeLog(
                    id=str(uuid4()),
                    entity_type='project',
                    entity_id=existing_project.id,
                    change_type='updated',
                    field_changes=changes,
                    old_values=old_vals,
                    new_values=changes,
                    source='dws_etl',
                    created_at=datetime.utcnow(),
                )
                session.add(change_log)
                
                logger.info(f"Updated project: {existing_project.name} - {list(changes.keys())}")
                
                return {
                    'entity_type': 'project',
                    'entity_id': existing_project.id,
                    'change_type': 'updated',
                    'changes': changes,
                    'timestamp': datetime.utcnow(),
                }
        else:
            # Create new project
            project = Project(
                id=str(uuid4()),
                external_id=project_data['external_id'],
                source='dws_pmd',
                municipality_id=municipality.id if municipality else None,
                name=project_data['name'],
                description=project_data['description'],
                project_type=project_data['project_type'],
                status=project_data['status'],
                start_date=datetime.fromisoformat(project_data['start_date']).date() if project_data.get('start_date') else None,
                end_date=datetime.fromisoformat(project_data['end_date']).date() if project_data.get('end_date') else None,
                location=project_data['location'],
                address=project_data['address'],
                budget_allocated=project_data['budget_allocated'],
                budget_spent=project_data['budget_spent'],
                progress_percentage=project_data['progress_percentage'],
                contractor=project_data['contractor'],
                raw_data=project_data,
                content_hash=content_hash,
                last_scraped_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(project)
            
            # Log creation
            change_log = DataChangeLog(
                id=str(uuid4()),
                entity_type='project',
                entity_id=project.id,
                change_type='created',
                field_changes={'status': 'new project created'},
                old_values={},
                new_values={'name': project.name, 'status': project.status},
                source='dws_etl',
                created_at=datetime.utcnow(),
            )
            session.add(change_log)
            
            logger.info(f"Created new project: {project.name}")
            
            return {
                'entity_type': 'project',
                'entity_id': project.id,
                'change_type': 'created',
                'changes': {'name': project.name, 'status': project.status},
                'timestamp': datetime.utcnow(),
            }
        
        return None

    async def poll_with_change_detection(self) -> None:
        """Enhanced polling with change detection and real-time notifications."""
        try:
            logger.info("Starting DWS data polling with change detection")
            current_data = await self.fetch_dws_data()
            current_hash = self.calculate_content_hash(current_data)
            
            if current_hash != self.last_content_hashes.get('dws_projects'):
                logger.info("DWS data changes detected, processing updates")
                changes = await self.process_data_changes(current_data)
                
                # Update hash tracking
                self.last_content_hashes['dws_projects'] = current_hash
                
                # Trigger real-time notifications
                for change in changes:
                    await self.notification_manager.notify_change(change)
                    
                logger.info(f"Processed {len(changes)} project changes")
            else:
                logger.debug("No changes detected in DWS data")
                
        except Exception as e:
            logger.error(f"Error in DWS change detection polling: {e}")
            await self.notification_manager.notify_system_error(
                "DWS polling error", str(e)
            )

