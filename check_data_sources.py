#!/usr/bin/env python3
"""
Script to check DWS and Treasury data sources and verify project counts
"""

import asyncio
import sys
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
import json
import re

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def check_dws_website():
    """Check the DWS Project Monitoring Dashboard website directly"""
    print("=== CHECKING DWS WEBSITE DIRECTLY ===")
    
    url = 'https://ws.dws.gov.za/pmd/level.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': 'https://ws.dws.gov.za/',
    }
    
    try:
        async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
            print(f"Fetching: {url}")
            response = await client.get(url)
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for any tables
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables on the page")
                
                # Look for project-related elements
                project_divs = soup.find_all('div', class_=re.compile(r'(project|item|card)', re.I))
                print(f"Found {len(project_divs)} potential project divs")
                
                # Look for any form elements or dropdowns
                selects = soup.find_all('select')
                print(f"Found {len(selects)} select dropdowns")
                
                for i, select in enumerate(selects[:3]):
                    options = select.find_all('option')
                    print(f"  Select {i+1}: {len(options)} options")
                    if select.get('id'):
                        print(f"    ID: {select.get('id')}")
                
                # Look for any data containers
                data_containers = soup.find_all(['div', 'span', 'td'], text=re.compile(r'(project|municipality|budget|million|billion)', re.I))
                print(f"Found {len(data_containers)} elements with project-related text")
                
                # Get page title and some sample text
                title = soup.title.string if soup.title else "No title"
                print(f"Page title: {title}")
                
                # Save a sample of the HTML for inspection
                with open("dws_sample.html", "w", encoding="utf-8") as f:
                    f.write(str(soup)[:5000])  # First 5000 characters
                print("Saved first 5KB of HTML to dws_sample.html")
                
            else:
                print(f"Failed to access DWS website: HTTP {response.status_code}")
                print(f"Response text: {response.text[:500]}")
                
    except Exception as e:
        print(f"Error accessing DWS website: {str(e)}")

async def check_treasury_api():
    """Check the Treasury API directly"""
    print("\n=== CHECKING TREASURY API DIRECTLY ===")
    
    base_url = 'https://municipaldata.treasury.gov.za/api'
    headers = {
        'User-Agent': 'Buka-Amanzi/3.0 Water Infrastructure Monitor',
    }
    
    try:
        async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
            
            # Check municipalities endpoint
            print("1. Checking municipalities endpoint...")
            muni_url = f"{base_url}/cubes/municipalities/facts"
            muni_params = {
                'cut': 'demarcation.type:"municipality"',
                'drilldown': 'municipality',
                'format': 'json'
            }
            
            response = await client.get(muni_url, params=muni_params)
            print(f"Municipalities API status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                municipalities = data.get('cells', [])
                print(f"Found {len(municipalities)} municipalities in Treasury API")
                
                # Show a few examples
                for i, item in enumerate(municipalities[:5]):
                    muni_data = item.get('municipality', {})
                    print(f"  {i+1}. {muni_data.get('name', 'Unknown')} ({muni_data.get('code', 'No Code')})")
            else:
                print(f"Failed to get municipalities: {response.text[:300]}")
            
            # Check a sample financial data endpoint
            print("\n2. Checking financial data endpoint for Cape Town...")
            budget_url = f"{base_url}/cubes/incexp/facts"
            budget_params = {
                'cut': 'municipality.demarcation_code:"CPT"|financial_year_end.year:2023',
                'drilldown': 'item.code|financial_period.period',
                'format': 'json'
            }
            
            response = await client.get(budget_url, params=budget_params)
            print(f"Financial data API status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('cells', [])
                print(f"Found {len(records)} financial records for Cape Town 2023")
            else:
                print(f"Failed to get financial data: {response.text[:300]}")
            
            # Check what cubes are available
            print("\n3. Checking available cubes...")
            cubes_url = f"{base_url}/cubes"
            response = await client.get(cubes_url)
            
            if response.status_code == 200:
                cubes_data = response.json()
                if isinstance(cubes_data, list):
                    print(f"Found {len(cubes_data)} available cubes:")
                    for cube in cubes_data[:10]:  # Show first 10
                        print(f"  - {cube.get('name', 'Unknown')}")
                elif isinstance(cubes_data, dict):
                    cubes = cubes_data.get('cubes', [])
                    print(f"Found {len(cubes)} available cubes:")
                    for cube in cubes[:10]:  # Show first 10
                        if isinstance(cube, str):
                            print(f"  - {cube}")
                        else:
                            print(f"  - {cube.get('name', cube)}")
            else:
                print(f"Failed to get cubes list: {response.text[:300]}")
                
    except Exception as e:
        print(f"Error accessing Treasury API: {str(e)}")

async def check_our_system():
    """Check what our system is currently retrieving"""
    print("\n=== CHECKING OUR SYSTEM'S RETRIEVAL ===")
    
    try:
        from app.etl.dws import EnhancedDWSMonitor
        from app.etl.treasury import MunicipalTreasuryETL
        from app.realtime.notifier import DataChangeNotifier
        
        notifier = DataChangeNotifier()
        
        # Check DWS data retrieval
        print("1. Checking our DWS data retrieval...")
        dws_monitor = EnhancedDWSMonitor(notifier)
        dws_data = await dws_monitor.fetch_dws_data()
        
        print(f"Our system retrieves {len(dws_data.get('projects', []))} DWS projects")
        print(f"Our system retrieves {len(dws_data.get('municipalities', []))} DWS municipalities")
        
        # Check if it's using real or mock data
        sample_project = dws_data.get('projects', [{}])[0] if dws_data.get('projects') else {}
        if 'DWS-WC-001' in str(sample_project.get('external_id', '')):
            print("STATUS: Using mock/fallback data")
        else:
            print("STATUS: Using real scraped data")
        
        # Check Treasury data retrieval
        print("\n2. Checking our Treasury data retrieval...")
        async with MunicipalTreasuryETL(notifier) as treasury_etl:
            municipalities = await treasury_etl.fetch_municipalities()
        
        print(f"Our system retrieves {len(municipalities)} Treasury municipalities")
        
        if municipalities:
            print("Sample Treasury municipalities:")
            for i, muni in enumerate(municipalities[:5]):
                print(f"  {i+1}. {muni.get('name', 'Unknown')} ({muni.get('code', 'No Code')})")
        else:
            print("No Treasury municipalities retrieved")
        
    except Exception as e:
        print(f"Error checking our system: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to run all checks"""
    print("PROJECT COUNT VERIFICATION SCRIPT")
    print("="*50)
    
    await check_dws_website()
    await check_treasury_api()
    await check_our_system()
    
    print("\n" + "="*50)
    print("SUMMARY AND RECOMMENDATIONS:")
    print("1. Check dws_sample.html to see what the DWS website actually contains")
    print("2. Compare Treasury API results with our system's retrieval")
    print("3. Verify if we're getting all available projects from both sources")
    print("4. Consider implementing pagination if sources have more data")

if __name__ == "__main__":
    asyncio.run(main())
