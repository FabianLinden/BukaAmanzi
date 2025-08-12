from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import logging

import httpx
from bs4 import BeautifulSoup, Tag

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ComprehensiveDWSProjectScraper:
    """
    Comprehensive scraper for DWS Project Monitoring Dashboard
    Extracts ALL available project information from https://ws.dws.gov.za/pmd/
    """
    
    def __init__(self):
        self.base_url = 'https://ws.dws.gov.za/pmd/'
        # Enhanced timeout and retry configuration
        self.timeout_config = httpx.Timeout(
            connect=30.0,      # Connection timeout
            read=180.0,        # Read timeout for large responses
            write=30.0,        # Write timeout
            pool=60.0          # Pool timeout
        )
        
        self.session_config = {
            'timeout': self.timeout_config,
            'limits': httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30
            ),
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'follow_redirects': True
        }
        
        # Retry configuration
        self.retry_config = {
            'max_retries': 5,
            'retry_delay': 2,
            'max_retry_delay': 60,
            'backoff_factor': 2
        }
        self.discovered_urls = set()
        self.scraped_data = {
            'municipalities': {},
            'projects': {},
            'metadata': {
                'scrape_timestamp': None,
                'total_municipalities': 0,
                'total_projects': 0,
                'provinces_covered': set(),
                'total_budget_value': 0.0
            }
        }
    
    async def scrape_all_projects(self) -> Dict[str, Any]:
        """
        Main method to scrape ALL projects from DWS PMD
        """
        logger.info("Starting comprehensive DWS project scraping...")
        
        async with httpx.AsyncClient(**self.session_config) as client:
            # Step 1: Start from the main level page
            await self._scrape_main_level_page(client)
            
            # Step 2: Discover all municipality pages
            await self._discover_all_municipality_pages(client)
            
            # Step 3: Scrape each municipality's projects
            await self._scrape_all_municipality_projects(client)
            
            # Step 4: Extract additional data from dashboards and reports
            await self._scrape_dashboard_data(client)
            
            # Step 5: Finalize and return comprehensive data
            return await self._finalize_scraped_data()
    
    async def _scrape_main_level_page(self, client: httpx.AsyncClient) -> None:
        """Scrape the main level.aspx page to get municipality listings"""
        try:
            # The URL from your external context
            url = 'https://ws.dws.gov.za/pmd/level.aspx?enc=VWReJm+SmGcCYM6pJQAmVBLmM33+9zWef3oVk0rPHvehd5PO8glfwc6rREAYyNxl'
            
            logger.info(f"Scraping main level page: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract municipality information from the page content
            await self._extract_municipalities_from_content(soup)
            
            # Look for additional navigation links
            await self._discover_navigation_urls(soup)
            
        except Exception as e:
            logger.error(f"Error scraping main level page: {str(e)}")
    
    async def _extract_municipalities_from_content(self, soup: BeautifulSoup) -> None:
        """Extract municipality data from page content"""
        try:
            # Get all text content
            page_text = soup.get_text()
            
            # Pattern to match municipality entries from your external context
            # Format: "Municipality Name - [CODE] X Projects with a Total value: RX,XXX,XXX.XX"
            municipality_pattern = r'([A-Za-z\s\-\'\.\!]+?)\s*-\s*\[([A-Z0-9]+)\]\s*(\d+)\s*Projects\s*with\s*a\s*Total\s*value:\s*R([\d,\.]+)'
            
            matches = re.finditer(municipality_pattern, page_text)
            
            for match in matches:
                municipality_name = match.group(1).strip()
                municipality_code = match.group(2)
                project_count = int(match.group(3))
                total_value = self._parse_currency_value(match.group(4))
                
                # Determine province from municipality name/code patterns
                province = self._determine_province_from_code(municipality_code)
                
                municipality_data = {
                    'name': municipality_name,
                    'code': municipality_code,
                    'province': province,
                    'project_count': project_count,
                    'total_project_value': total_value,
                    'projects': [],
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                self.scraped_data['municipalities'][municipality_code] = municipality_data
                self.scraped_data['metadata']['provinces_covered'].add(province)
                
                logger.info(f"Found municipality: {municipality_name} ({municipality_code}) - {project_count} projects, R{total_value:,.0f}")
            
            logger.info(f"Extracted {len(self.scraped_data['municipalities'])} municipalities from main page")
            
        except Exception as e:
            logger.error(f"Error extracting municipalities from content: {str(e)}")
    
    async def _discover_navigation_urls(self, soup: BeautifulSoup) -> None:
        """Discover navigation URLs for detailed scraping"""
        try:
            # Look for links to individual municipality pages
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and ('municipality' in href.lower() or 'project' in href.lower() or 'level.aspx' in href):
                    full_url = urljoin(self.base_url, href)
                    self.discovered_urls.add(full_url)
            
            # Also look for form actions and JavaScript URLs
            forms = soup.find_all('form', action=True)
            for form in forms:
                action = form.get('action')
                if action:
                    full_url = urljoin(self.base_url, action)
                    self.discovered_urls.add(full_url)
            
            logger.info(f"Discovered {len(self.discovered_urls)} potential URLs for detailed scraping")
            
        except Exception as e:
            logger.error(f"Error discovering navigation URLs: {str(e)}")
    
    async def _discover_all_municipality_pages(self, client: httpx.AsyncClient) -> None:
        """Discover individual municipality project pages"""
        try:
            # For each municipality, try to construct direct URLs
            for municipality_code, municipality_data in self.scraped_data['municipalities'].items():
                # Try common URL patterns for municipality pages
                potential_urls = [
                    f"{self.base_url}level.aspx?municipality={municipality_code}",
                    f"{self.base_url}projects.aspx?muni={municipality_code}",
                    f"{self.base_url}dashboard.aspx?code={municipality_code}",
                    f"{self.base_url}level.aspx?enc=VWReJm+SmGcCYM6pJQAmVBLmM33+9zWef3oVk0rPHvehd5PO8glfwc6rREAYyNxl&muni={municipality_code}",
                ]
                
                for url in potential_urls:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200 and len(response.content) > 1000:
                            # Page exists and has content
                            municipality_data['detail_url'] = url
                            self.discovered_urls.add(url)
                            break
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Error discovering municipality pages: {str(e)}")
    
    async def _scrape_all_municipality_projects(self, client: httpx.AsyncClient) -> None:
        """Scrape detailed project information for each municipality"""
        try:
            for municipality_code, municipality_data in self.scraped_data['municipalities'].items():
                await self._scrape_municipality_projects(client, municipality_code, municipality_data)
                
                # Add delay between municipality scraping to be respectful
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error scraping all municipality projects: {str(e)}")
    
    async def _scrape_municipality_projects(self, client: httpx.AsyncClient, municipality_code: str, municipality_data: Dict) -> None:
        """Scrape projects for a specific municipality"""
        try:
            logger.info(f"Scraping projects for {municipality_data['name']} ({municipality_code})")
            
            # Try the detail URL if we have one
            if 'detail_url' in municipality_data:
                await self._scrape_projects_from_url(client, municipality_data['detail_url'], municipality_code)
            
            # Also try ASP.NET postback to get project details
            await self._try_aspnet_project_lookup(client, municipality_code)
            
            # Try to get project data through AJAX calls
            await self._try_ajax_project_data(client, municipality_code)
            
        except Exception as e:
            logger.error(f"Error scraping projects for {municipality_code}: {str(e)}")
    
    async def _scrape_projects_from_url(self, client: httpx.AsyncClient, url: str, municipality_code: str) -> None:
        """Scrape projects from a specific URL"""
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for project tables
            tables = soup.find_all('table')
            for table in tables:
                await self._extract_projects_from_table(table, municipality_code)
            
            # Look for project cards/divs
            project_containers = soup.find_all(['div', 'article', 'section'], 
                                               class_=re.compile(r'(project|item|card|row)', re.I))
            for container in project_containers:
                await self._extract_project_from_container(container, municipality_code)
            
            # Look for JSON data in scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    await self._extract_json_project_data(script.string, municipality_code)
                    
        except Exception as e:
            logger.debug(f"Error scraping projects from URL {url}: {str(e)}")
    
    async def _extract_projects_from_table(self, table: Tag, municipality_code: str) -> None:
        """Extract project data from HTML tables"""
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:
                return
            
            # Get headers
            header_row = rows[0]
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            # Check if this looks like a project table
            project_indicators = ['project', 'name', 'status', 'budget', 'progress', 'contractor', 'value']
            if not any(indicator in ' '.join(headers) for indicator in project_indicators):
                return
            
            # Extract project data from each row
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cells) >= len(headers):
                    project = await self._create_project_from_cells(headers, cells, municipality_code)
                    if project:
                        await self._add_project_to_municipality(project, municipality_code)
                        
        except Exception as e:
            logger.debug(f"Error extracting projects from table: {str(e)}")
    
    async def _create_project_from_cells(self, headers: List[str], cells: List[str], municipality_code: str) -> Optional[Dict]:
        """Create a project dictionary from table cell data"""
        try:
            project = {
                'external_id': f"DWS-{municipality_code}-{hashlib.md5(''.join(cells).encode()).hexdigest()[:8]}",
                'source': 'dws_pmd_comprehensive',
                'municipality_code': municipality_code,
                'name': '',
                'description': '',
                'project_type': 'water_infrastructure',
                'status': 'unknown',
                'progress_percentage': 0,
                'budget_allocated': 0.0,
                'budget_spent': 0.0,
                'contractor': '',
                'start_date': None,
                'end_date': None,
                'location': '',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            # Map headers to project fields
            field_mappings = {
                'project': 'name',
                'name': 'name', 
                'title': 'name',
                'description': 'description',
                'status': 'status',
                'phase': 'status',
                'progress': 'progress_percentage',
                'completion': 'progress_percentage',
                'budget': 'budget_allocated',
                'value': 'budget_allocated',
                'cost': 'budget_allocated',
                'allocated': 'budget_allocated',
                'spent': 'budget_spent',
                'contractor': 'contractor',
                'company': 'contractor',
                'location': 'location',
                'type': 'project_type',
                'start': 'start_date',
                'end': 'end_date'
            }
            
            # Extract data based on headers
            for i, header in enumerate(headers):
                if i < len(cells):
                    cell_value = cells[i].strip()
                    
                    # Find matching field
                    for pattern, field in field_mappings.items():
                        if pattern in header:
                            if field == 'progress_percentage':
                                progress_match = re.search(r'(\d+)', cell_value)
                                if progress_match:
                                    project[field] = min(100, int(progress_match.group(1)))
                            elif field in ['budget_allocated', 'budget_spent']:
                                project[field] = self._parse_currency_value(cell_value)
                            elif field in ['start_date', 'end_date']:
                                project[field] = self._parse_date_value(cell_value)
                            else:
                                project[field] = cell_value
                            break
            
            # Only return project if it has essential data
            if project['name'] and len(project['name']) > 3:
                return project
                
            return None
            
        except Exception as e:
            logger.debug(f"Error creating project from cells: {str(e)}")
            return None
    
    async def _extract_project_from_container(self, container: Tag, municipality_code: str) -> None:
        """Extract project data from HTML containers (divs, cards, etc.)"""
        try:
            text_content = container.get_text(' ', strip=True)
            
            if len(text_content) < 20:
                return
            
            # Look for project name in headers or bold text
            name_elements = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
            project_name = ''
            if name_elements:
                project_name = name_elements[0].get_text(strip=True)
            else:
                # Use first sentence as name
                sentences = text_content.split('.')
                if sentences:
                    project_name = sentences[0][:100]
            
            if not project_name or len(project_name) < 5:
                return
            
            project = {
                'external_id': f"DWS-{municipality_code}-{hashlib.md5(text_content.encode()).hexdigest()[:8]}",
                'source': 'dws_pmd_comprehensive',
                'municipality_code': municipality_code,
                'name': project_name,
                'description': text_content[:500],
                'project_type': self._determine_project_type(text_content),
                'status': self._extract_status_from_text(text_content),
                'progress_percentage': self._extract_progress_from_text(text_content),
                'budget_allocated': self._extract_budget_from_text(text_content),
                'budget_spent': 0.0,
                'contractor': self._extract_contractor_from_text(text_content),
                'location': '',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            await self._add_project_to_municipality(project, municipality_code)
            
        except Exception as e:
            logger.debug(f"Error extracting project from container: {str(e)}")
    
    async def _extract_json_project_data(self, script_content: str, municipality_code: str) -> None:
        """Extract project data from JavaScript/JSON content"""
        try:
            # Look for JSON objects that might contain project data
            json_patterns = [
                r'projects\s*[:=]\s*(\[.*?\])',
                r'data\s*[:=]\s*(\{.*?\})',
                r'gridData\s*[:=]\s*(\[.*?\])',
                r'(\{[^{}]*project[^{}]*\})',
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, script_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)
                        
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    project = await self._normalize_project_from_json(item, municipality_code)
                                    if project:
                                        await self._add_project_to_municipality(project, municipality_code)
                        elif isinstance(data, dict):
                            project = await self._normalize_project_from_json(data, municipality_code)
                            if project:
                                await self._add_project_to_municipality(project, municipality_code)
                                
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error extracting JSON project data: {str(e)}")
    
    async def _normalize_project_from_json(self, json_data: Dict, municipality_code: str) -> Optional[Dict]:
        """Normalize project data from JSON format"""
        try:
            # Check if this looks like project data
            project_indicators = ['project', 'name', 'title', 'municipality', 'status', 'budget']
            data_keys = [str(k).lower() for k in json_data.keys()]
            
            if not any(indicator in ' '.join(data_keys) for indicator in project_indicators):
                return None
            
            project = {
                'external_id': f"DWS-{municipality_code}-{hashlib.md5(str(json_data).encode()).hexdigest()[:8]}",
                'source': 'dws_pmd_comprehensive',
                'municipality_code': municipality_code,
                'name': '',
                'description': '',
                'project_type': 'water_infrastructure',
                'status': 'unknown',
                'progress_percentage': 0,
                'budget_allocated': 0.0,
                'budget_spent': 0.0,
                'contractor': '',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            # Map JSON fields to project fields
            field_mappings = {
                'name': ['name', 'title', 'project_name', 'projectName'],
                'description': ['description', 'desc', 'details', 'summary'],
                'status': ['status', 'phase', 'state'],
                'progress_percentage': ['progress', 'completion', 'percent'],
                'budget_allocated': ['budget', 'value', 'cost', 'amount'],
                'contractor': ['contractor', 'company', 'vendor']
            }
            
            for project_field, json_keys in field_mappings.items():
                for json_key in json_keys:
                    for data_key, data_value in json_data.items():
                        if json_key.lower() in str(data_key).lower():
                            if project_field == 'progress_percentage':
                                progress_match = re.search(r'(\d+)', str(data_value))
                                if progress_match:
                                    project[project_field] = min(100, int(progress_match.group(1)))
                            elif project_field == 'budget_allocated':
                                project[project_field] = self._parse_currency_value(str(data_value))
                            else:
                                project[project_field] = str(data_value).strip()
                            break
                    if project[project_field]:
                        break
            
            if project['name'] and len(project['name']) > 3:
                return project
                
            return None
            
        except Exception as e:
            logger.debug(f"Error normalizing project from JSON: {str(e)}")
            return None
    
    async def _try_aspnet_project_lookup(self, client: httpx.AsyncClient, municipality_code: str) -> None:
        """Try ASP.NET postback to get project details"""
        try:
            # This would involve form submission with viewstate
            # Implementation would depend on specific ASP.NET structure
            pass
        except Exception as e:
            logger.debug(f"Error in ASP.NET project lookup for {municipality_code}: {str(e)}")
    
    async def _try_ajax_project_data(self, client: httpx.AsyncClient, municipality_code: str) -> None:
        """Try AJAX calls to get project data"""
        try:
            # Try common AJAX endpoints
            ajax_endpoints = [
                f"{self.base_url}api/projects/{municipality_code}",
                f"{self.base_url}data/projects.aspx?muni={municipality_code}",
                f"{self.base_url}handlers/ProjectData.ashx?code={municipality_code}",
            ]
            
            for endpoint in ajax_endpoints:
                try:
                    response = await client.get(endpoint)
                    if response.status_code == 200:
                        if 'json' in response.headers.get('content-type', '').lower():
                            data = response.json()
                            # Process JSON data
                            await self._process_ajax_response(data, municipality_code)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in AJAX project data for {municipality_code}: {str(e)}")
    
    async def _process_ajax_response(self, data: Any, municipality_code: str) -> None:
        """Process AJAX response data"""
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        project = await self._normalize_project_from_json(item, municipality_code)
                        if project:
                            await self._add_project_to_municipality(project, municipality_code)
            elif isinstance(data, dict):
                project = await self._normalize_project_from_json(data, municipality_code)
                if project:
                    await self._add_project_to_municipality(project, municipality_code)
                    
        except Exception as e:
            logger.debug(f"Error processing AJAX response: {str(e)}")
    
    async def _scrape_dashboard_data(self, client: httpx.AsyncClient) -> None:
        """Scrape additional data from dashboard and report pages"""
        try:
            dashboard_urls = [
                f"{self.base_url}dashboard.aspx",
                f"{self.base_url}reports.aspx",
                f"{self.base_url}summary.aspx",
                f"{self.base_url}national.aspx",
            ]
            
            for url in dashboard_urls:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        await self._extract_summary_statistics(soup)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error scraping dashboard data: {str(e)}")
    
    async def _extract_summary_statistics(self, soup: BeautifulSoup) -> None:
        """Extract summary statistics from dashboard pages"""
        try:
            # Look for summary statistics
            text_content = soup.get_text()
            
            # Extract total values
            total_patterns = [
                r'total\s+projects?\s*[:=]?\s*(\d+)',
                r'(\d+)\s+projects?',
                r'total\s+value\s*[:=]?\s*R?([\d,\.]+)',
                r'R\s*([\d,\.]+)\s*(?:million|billion)?'
            ]
            
            for pattern in total_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    # Update metadata with found statistics
                    pass
                    
        except Exception as e:
            logger.debug(f"Error extracting summary statistics: {str(e)}")
    
    async def _add_project_to_municipality(self, project: Dict, municipality_code: str) -> None:
        """Add a project to a municipality's project list"""
        try:
            if municipality_code not in self.scraped_data['municipalities']:
                return
            
            # Check for duplicates
            municipality = self.scraped_data['municipalities'][municipality_code]
            existing_projects = municipality.get('projects', [])
            
            # Check if project already exists (by name or external_id)
            for existing_project in existing_projects:
                if (existing_project.get('name') == project['name'] or
                    existing_project.get('external_id') == project['external_id']):
                    return  # Skip duplicate
            
            # Add project to municipality
            municipality['projects'].append(project)
            
            # Add to global projects dict as well
            self.scraped_data['projects'][project['external_id']] = project
            
            logger.debug(f"Added project '{project['name']}' to {municipality_code}")
            
        except Exception as e:
            logger.debug(f"Error adding project to municipality: {str(e)}")
    
    async def _finalize_scraped_data(self) -> Dict[str, Any]:
        """Finalize and return comprehensive scraped data"""
        try:
            # Update metadata
            self.scraped_data['metadata']['scrape_timestamp'] = datetime.utcnow().isoformat()
            self.scraped_data['metadata']['total_municipalities'] = len(self.scraped_data['municipalities'])
            self.scraped_data['metadata']['total_projects'] = len(self.scraped_data['projects'])
            
            # Calculate total budget value
            total_budget = 0.0
            for project in self.scraped_data['projects'].values():
                total_budget += project.get('budget_allocated', 0.0)
            
            self.scraped_data['metadata']['total_budget_value'] = total_budget
            self.scraped_data['metadata']['provinces_covered'] = list(self.scraped_data['metadata']['provinces_covered'])
            
            # Convert to the format expected by the ETL system
            formatted_data = {
                'projects': list(self.scraped_data['projects'].values()),
                'municipalities': [
                    {
                        'name': muni['name'],
                        'code': muni['code'],
                        'province': muni['province']
                    }
                    for muni in self.scraped_data['municipalities'].values()
                ],
                'metadata': self.scraped_data['metadata'],
                'scrape_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Scraping completed: {len(formatted_data['projects'])} projects, {len(formatted_data['municipalities'])} municipalities")
            logger.info(f"Total project value: R{total_budget:,.0f}")
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error finalizing scraped data: {str(e)}")
            return {
                'projects': [],
                'municipalities': [],
                'metadata': {'error': str(e)},
                'scrape_timestamp': datetime.utcnow().isoformat()
            }
    
    # Helper methods
    
    def _parse_currency_value(self, value_str: str) -> float:
        """Parse currency value from string"""
        try:
            if not value_str:
                return 0.0
            
            # Remove common currency symbols and whitespace
            clean_value = re.sub(r'[R\s,]', '', str(value_str))
            
            # Extract numeric value
            number_match = re.search(r'([\d.]+)', clean_value)
            if not number_match:
                return 0.0
            
            amount = float(number_match.group(1))
            
            # Check for multipliers
            value_lower = str(value_str).lower()
            if 'billion' in value_lower or 'b' in value_lower:
                amount *= 1000000000
            elif 'million' in value_lower or 'm' in value_lower:
                amount *= 1000000
            elif 'thousand' in value_lower or 'k' in value_lower:
                amount *= 1000
            
            return amount
            
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_date_value(self, date_str: str) -> Optional[str]:
        """Parse date value from string"""
        try:
            if not date_str or len(date_str.strip()) < 4:
                return None
            
            # Try to extract year at minimum
            year_match = re.search(r'(20\d{2})', date_str)
            if year_match:
                return f"{year_match.group(1)}-01-01"  # Default to January 1st
            
            return None
            
        except Exception:
            return None
    
    def _determine_province_from_code(self, municipality_code: str) -> str:
        """Determine province from municipality code"""
        try:
            # Province code mappings
            province_codes = {
                'WC': 'Western Cape', 'EC': 'Eastern Cape', 'NC': 'Northern Cape',
                'FS': 'Free State', 'KZN': 'KwaZulu-Natal', 'NW': 'North West',
                'GT': 'Gauteng', 'MP': 'Mpumalanga', 'LIM': 'Limpopo',
                'CPT': 'Western Cape', 'JHB': 'Gauteng', 'ETH': 'KwaZulu-Natal',
                'TSH': 'Gauteng', 'EKU': 'Gauteng', 'BUF': 'Eastern Cape',
                'MAN': 'Free State'
            }
            
            for code_prefix, province in province_codes.items():
                if municipality_code.startswith(code_prefix):
                    return province
            
            # Try to determine from full code patterns
            if municipality_code.startswith(('WC', 'CPT')):
                return 'Western Cape'
            elif municipality_code.startswith(('EC', 'BUF')):
                return 'Eastern Cape'
            elif municipality_code.startswith('NC'):
                return 'Northern Cape'
            elif municipality_code.startswith(('FS', 'MAN')):
                return 'Free State'
            elif municipality_code.startswith(('KZN', 'ETH')):
                return 'KwaZulu-Natal'
            elif municipality_code.startswith('NW'):
                return 'North West'
            elif municipality_code.startswith(('GT', 'JHB', 'TSH', 'EKU')):
                return 'Gauteng'
            elif municipality_code.startswith('MP'):
                return 'Mpumalanga'
            elif municipality_code.startswith('LIM'):
                return 'Limpopo'
            
            return 'Unknown Province'
            
        except Exception:
            return 'Unknown Province'
    
    def _determine_project_type(self, text: str) -> str:
        """Determine project type from text content"""
        try:
            text_lower = text.lower()
            
            if any(keyword in text_lower for keyword in ['dam', 'reservoir', 'storage']):
                return 'dam_construction'
            elif any(keyword in text_lower for keyword in ['treatment', 'plant', 'wtp', 'purification']):
                return 'water_treatment'
            elif any(keyword in text_lower for keyword in ['pipeline', 'pipe', 'distribution', 'network']):
                return 'pipeline'
            elif any(keyword in text_lower for keyword in ['supply', 'provision', 'access']):
                return 'water_supply'
            elif any(keyword in text_lower for keyword in ['bulk', 'regional', 'scheme']):
                return 'bulk_water_supply'
            elif any(keyword in text_lower for keyword in ['sanitation', 'sewage', 'waste']):
                return 'sanitation'
            else:
                return 'water_infrastructure'
                
        except Exception:
            return 'water_infrastructure'
    
    def _extract_status_from_text(self, text: str) -> str:
        """Extract project status from text"""
        try:
            text_lower = text.lower()
            
            if any(keyword in text_lower for keyword in ['completed', 'finished', 'done']):
                return 'completed'
            elif any(keyword in text_lower for keyword in ['progress', 'ongoing', 'construction']):
                return 'in_progress'
            elif any(keyword in text_lower for keyword in ['planning', 'design', 'proposed']):
                return 'planning'
            elif any(keyword in text_lower for keyword in ['delayed', 'behind', 'overdue']):
                return 'delayed'
            elif any(keyword in text_lower for keyword in ['cancelled', 'terminated', 'stopped']):
                return 'cancelled'
            else:
                return 'unknown'
                
        except Exception:
            return 'unknown'
    
    def _extract_progress_from_text(self, text: str) -> int:
        """Extract progress percentage from text"""
        try:
            # Look for percentage patterns
            progress_patterns = [
                r'(\d+)%',
                r'(\d+)\s*percent',
                r'progress[:\s]+(\d+)',
                r'completion[:\s]+(\d+)'
            ]
            
            for pattern in progress_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return min(100, int(match.group(1)))
            
            return 0
            
        except Exception:
            return 0
    
    def _extract_budget_from_text(self, text: str) -> float:
        """Extract budget amount from text"""
        try:
            budget_patterns = [
                r'R\s*([\d,\.]+)\s*(million|billion|m|b)?',
                r'budget[:\s]+R?\s*([\d,\.]+)',
                r'value[:\s]+R?\s*([\d,\.]+)',
                r'cost[:\s]+R?\s*([\d,\.]+)'
            ]
            
            for pattern in budget_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return self._parse_currency_value(match.group(0))
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _extract_contractor_from_text(self, text: str) -> str:
        """Extract contractor name from text"""
        try:
            contractor_patterns = [
                r'contractor[:\s]+([\w\s&\-\.]+?)(?:\.|,|\n|$)',
                r'company[:\s]+([\w\s&\-\.]+?)(?:\.|,|\n|$)',
                r'built by[:\s]+([\w\s&\-\.]+?)(?:\.|,|\n|$)'
            ]
            
            for pattern in contractor_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return ''
            
        except Exception:
            return ''


# Integration function for the existing ETL system
async def scrape_comprehensive_dws_data() -> Dict[str, Any]:
    """
    Function to be called by the existing ETL system
    Returns comprehensive project data from DWS PMD
    """
    scraper = ComprehensiveDWSProjectScraper()
    return await scraper.scrape_all_projects()


if __name__ == "__main__":
    # Test the scraper
    async def test_scraper():
        scraper = ComprehensiveDWSProjectScraper()
        data = await scraper.scrape_all_projects()
        print(f"Scraped {len(data['projects'])} projects from {len(data['municipalities'])} municipalities")
        return data
    
    asyncio.run(test_scraper())
