#!/usr/bin/env python3
"""
Detailed analysis of DWS website structure to fix scraping logic
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import re

async def analyze_dws_structure():
    """Analyze DWS website structure in detail"""
    print("=== DETAILED DWS WEBSITE ANALYSIS ===")
    
    url = 'https://ws.dws.gov.za/pmd/level.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Referer': 'https://ws.dws.gov.za/',
    }
    
    try:
        async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Save full HTML for analysis
                with open("dws_full_analysis.html", "w", encoding="utf-8") as f:
                    f.write(str(soup.prettify()))
                print("Saved full HTML to dws_full_analysis.html")
                
                # Look for all forms and their controls
                forms = soup.find_all('form')
                print(f"\nFound {len(forms)} forms:")
                for i, form in enumerate(forms):
                    print(f"  Form {i+1}: action='{form.get('action', 'N/A')}' method='{form.get('method', 'GET')}'")
                    
                    # Find controls in form
                    inputs = form.find_all(['input', 'select', 'textarea'])
                    for inp in inputs[:10]:  # Show first 10 inputs
                        inp_type = inp.name
                        inp_id = inp.get('id', 'no-id')
                        inp_name = inp.get('name', 'no-name')
                        if inp.name == 'select':
                            options = inp.find_all('option')
                            print(f"    {inp_type}: id='{inp_id}' name='{inp_name}' ({len(options)} options)")
                        else:
                            print(f"    {inp_type}: id='{inp_id}' name='{inp_name}'")
                
                # Look for JavaScript that might load data
                scripts = soup.find_all('script')
                print(f"\nFound {len(scripts)} script tags")
                
                js_with_data = []
                for i, script in enumerate(scripts):
                    script_content = script.string or ""
                    if any(keyword in script_content.lower() for keyword in ['project', 'data', 'ajax', 'json', 'api']):
                        js_with_data.append((i, script_content[:200]))
                
                print(f"Scripts with potential data loading ({len(js_with_data)}):")
                for i, content in js_with_data:
                    print(f"  Script {i}: {content}...")
                
                # Look for DevExpress controls (common in ASP.NET)
                dx_controls = soup.find_all(attrs={'id': re.compile(r'dx', re.I)})
                print(f"\nFound {len(dx_controls)} potential DevExpress controls:")
                for control in dx_controls[:10]:
                    print(f"  {control.name}: id='{control.get('id')}' class='{control.get('class')}'")
                
                # Look for data tables or grids
                data_containers = soup.find_all(['div', 'table'], class_=re.compile(r'(grid|data|table|project)', re.I))
                print(f"\nFound {len(data_containers)} potential data containers:")
                for container in data_containers:
                    classes = container.get('class', [])
                    print(f"  {container.name}: class={classes} id='{container.get('id', 'no-id')}'")
                    
                    # Check if it has data rows
                    rows = container.find_all(['tr', 'div'], class_=re.compile(r'(row|item)', re.I))
                    if rows:
                        print(f"    Contains {len(rows)} potential data rows")
                
                # Look for any AJAX endpoints in JavaScript
                all_js = " ".join([script.string or "" for script in scripts])
                ajax_patterns = [
                    r'url\s*:\s*["\']([^"\']+)["\']',
                    r'\.get\(["\']([^"\']+)["\']',
                    r'\.post\(["\']([^"\']+)["\']',
                    r'ajax\(["\']([^"\']+)["\']',
                ]
                
                endpoints = set()
                for pattern in ajax_patterns:
                    matches = re.finditer(pattern, all_js, re.I)
                    for match in matches:
                        endpoint = match.group(1)
                        if endpoint.startswith(('/', 'http')) and not endpoint.endswith(('.js', '.css')):
                            endpoints.add(endpoint)
                
                print(f"\nPotential AJAX endpoints found ({len(endpoints)}):")
                for endpoint in list(endpoints)[:10]:
                    print(f"  {endpoint}")
                
                return {
                    'forms': len(forms),
                    'scripts': len(scripts),
                    'data_containers': len(data_containers),
                    'ajax_endpoints': list(endpoints)[:10]
                }
                
    except Exception as e:
        print(f"Error: {e}")
        return None

async def test_treasury_api_detailed():
    """Test Treasury API with different parameters"""
    print("\n=== DETAILED TREASURY API TESTING ===")
    
    base_url = 'https://municipaldata.treasury.gov.za/api'
    headers = {'User-Agent': 'Buka-Amanzi/3.0 Water Infrastructure Monitor'}
    
    try:
        async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
            
            # Test 1: Get available cubes
            print("1. Testing /cubes endpoint...")
            try:
                response = await client.get(f"{base_url}/cubes")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        cubes = data
                    else:
                        cubes = data.get('cubes', data.get('data', []))
                    print(f"   Available cubes: {len(cubes)}")
                    for cube in cubes[:5]:
                        if isinstance(cube, str):
                            print(f"     - {cube}")
                        else:
                            print(f"     - {cube.get('name', cube)}")
                else:
                    print(f"   Error: {response.text[:100]}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            # Test 2: Try different municipality endpoints
            print("\n2. Testing municipalities endpoint variations...")
            
            test_endpoints = [
                ('municipalities/facts', {'format': 'json', 'page_size': '50'}),
                ('municipalities/facts', {'format': 'json', 'page': '0', 'pagesize': '50'}),
                ('municipalities/facts', {'format': 'json'}),
                ('municipalities/members', {'format': 'json'}),
                ('cubes/municipalities/facts', {'format': 'json', 'drilldown': 'municipality'}),
                ('cubes/municipalities/facts', {'format': 'json', 'drilldown': 'municipality', 'pagesize': '100'}),
            ]
            
            for endpoint, params in test_endpoints:
                try:
                    url = f"{base_url}/{endpoint}"
                    response = await client.get(url, params=params)
                    print(f"   {endpoint} -> Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Try different ways to count results
                        counts = []
                        if isinstance(data, dict):
                            if 'cells' in data:
                                counts.append(f"cells: {len(data['cells'])}")
                            if 'data' in data:
                                counts.append(f"data: {len(data['data']) if isinstance(data['data'], list) else 'not list'}")
                            if 'summary' in data:
                                summary = data['summary']
                                if isinstance(summary, dict) and 'count' in summary:
                                    counts.append(f"summary.count: {summary['count']}")
                        elif isinstance(data, list):
                            counts.append(f"list length: {len(data)}")
                        
                        if counts:
                            print(f"     Results: {', '.join(counts)}")
                        else:
                            print(f"     Data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
                    
                    elif response.status_code != 500:
                        print(f"     Response: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"     Exception: {e}")
            
            # Test 3: Try to find project-related endpoints
            print("\n3. Looking for project-related cubes...")
            try:
                response = await client.get(f"{base_url}/cubes")
                if response.status_code == 200:
                    data = response.json()
                    cubes = data if isinstance(data, list) else data.get('cubes', [])
                    
                    project_keywords = ['project', 'capital', 'infrastructure', 'capex', 'expenditure']
                    matching_cubes = []
                    
                    for cube in cubes:
                        cube_name = cube if isinstance(cube, str) else cube.get('name', str(cube))
                        if any(keyword in cube_name.lower() for keyword in project_keywords):
                            matching_cubes.append(cube_name)
                    
                    print(f"   Found {len(matching_cubes)} potentially relevant cubes:")
                    for cube in matching_cubes:
                        print(f"     - {cube}")
                        
                        # Test the cube
                        try:
                            cube_response = await client.get(f"{base_url}/cubes/{cube}/facts", 
                                                           params={'format': 'json', 'page_size': '10'})
                            if cube_response.status_code == 200:
                                cube_data = cube_response.json()
                                cell_count = len(cube_data.get('cells', []))
                                print(f"       -> {cell_count} records available")
                            else:
                                print(f"       -> Status: {cube_response.status_code}")
                        except:
                            print(f"       -> Error testing cube")
                            
            except Exception as e:
                print(f"   Exception: {e}")
                
    except Exception as e:
        print(f"Overall error: {e}")

async def main():
    """Main analysis function"""
    print("COMPREHENSIVE WEBSITE STRUCTURE ANALYSIS")
    print("="*60)
    
    dws_analysis = await analyze_dws_structure()
    await test_treasury_api_detailed()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print("Check dws_full_analysis.html for detailed website structure")

if __name__ == "__main__":
    asyncio.run(main())
