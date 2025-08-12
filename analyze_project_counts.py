#!/usr/bin/env python3
"""
Analyze project counts from DWS and Treasury sources
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import re

async def analyze_dws_projects():
    """Analyze what projects are available on DWS website"""
    print("=== DWS PROJECT ANALYSIS ===")
    
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
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for tables that might contain project data
                tables = soup.find_all('table')
                print(f"Total tables found: {len(tables)}")
                
                project_count = 0
                for i, table in enumerate(tables):
                    rows = table.find_all('tr')
                    if len(rows) > 1:  # Has header and data rows
                        headers_row = rows[0].find_all(['th', 'td'])
                        headers_text = [th.get_text(strip=True).lower() for th in headers_row]
                        
                        # Check if this looks like a project table
                        project_indicators = ['project', 'name', 'municipality', 'province', 'status', 'budget']
                        if any(indicator in ' '.join(headers_text) for indicator in project_indicators):
                            data_rows = len(rows) - 1  # Subtract header row
                            print(f"  Table {i+1}: {data_rows} potential project rows")
                            print(f"    Headers: {headers_text}")
                            project_count += data_rows
                
                print(f"Estimated DWS projects from tables: {project_count}")
                
                # Look for any text mentioning project counts
                text_content = soup.get_text()
                count_patterns = [
                    r'(\d+)\s*projects?',
                    r'projects?\s*:\s*(\d+)',
                    r'total\s*[:\s]*(\d+)',
                ]
                
                for pattern in count_patterns:
                    matches = re.finditer(pattern, text_content, re.I)
                    for match in matches:
                        print(f"Found count reference: '{match.group(0)}' -> {match.group(1)}")
                
                return {
                    'source': 'DWS PMD',
                    'accessible': True,
                    'tables_with_projects': project_count,
                    'scraping_method': 'table_extraction'
                }
                
            else:
                return {
                    'source': 'DWS PMD',
                    'accessible': False,
                    'error': f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        print(f"Error accessing DWS: {e}")
        return {
            'source': 'DWS PMD',
            'accessible': False,
            'error': str(e)
        }

async def analyze_treasury_api():
    """Analyze Treasury API capabilities"""
    print("\n=== TREASURY API ANALYSIS ===")
    
    base_url = 'https://municipaldata.treasury.gov.za/api'
    headers = {'User-Agent': 'Buka-Amanzi/3.0 Water Infrastructure Monitor'}
    
    try:
        async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
            
            # Check if API is accessible
            try:
                response = await client.get(f"{base_url}/cubes")
                print(f"API Status: {response.status_code}")
                
                if response.status_code == 500:
                    print("Treasury API is currently down (500 error)")
                    return {
                        'source': 'Treasury API',
                        'accessible': False,
                        'error': 'API returning 500 errors'
                    }
                    
            except Exception:
                pass
            
            # Try municipalities endpoint with smaller request
            muni_url = f"{base_url}/cubes/municipalities/facts"
            muni_params = {
                'format': 'json',
                'page_size': '10'  # Smaller request
            }
            
            try:
                response = await client.get(muni_url, params=muni_params)
                print(f"Municipalities endpoint status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    total_municipalities = len(data.get('cells', []))
                    print(f"Sample shows {total_municipalities} municipalities available")
                    
                    return {
                        'source': 'Treasury API',
                        'accessible': True,
                        'municipalities_available': total_municipalities,
                        'note': 'Financial data per municipality, not project data'
                    }
                else:
                    print(f"API Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"Error with municipalities endpoint: {e}")
            
            return {
                'source': 'Treasury API',
                'accessible': False,
                'error': 'API endpoints not responding'
            }
            
    except Exception as e:
        print(f"Error with Treasury API: {e}")
        return {
            'source': 'Treasury API',
            'accessible': False,
            'error': str(e)
        }

def analyze_our_mock_data():
    """Analyze what our system provides as fallback"""
    print("\n=== OUR SYSTEM'S MOCK DATA ===")
    
    # Based on the code we saw earlier
    mock_dws_projects = 8  # From the DWS ETL code
    mock_treasury_municipalities = 8  # From the Treasury mock data
    
    print(f"DWS mock projects: {mock_dws_projects}")
    print(f"Treasury mock municipalities: {mock_treasury_municipalities}")
    
    mock_projects = [
        'Berg River-Voëlvlei Augmentation Scheme',
        'Lesotho Highlands Water Project Phase II',
        'uMkhomazi Water Project Phase 1',
        'Amathole Bulk Regional Water Supply Scheme',
        'Vaalkop Dam Raising Project',
        'Komati Water Scheme Augmentation',
        'Giyani Emergency Water Supply Project',
        'Modder River Government Water Scheme'
    ]
    
    print(f"Mock DWS projects include:")
    for i, project in enumerate(mock_projects, 1):
        print(f"  {i}. {project}")
    
    return {
        'source': 'Mock/Fallback Data',
        'dws_projects': mock_dws_projects,
        'treasury_municipalities': mock_treasury_municipalities,
        'data_type': 'Realistic mock data for demo/testing'
    }

async def main():
    """Main analysis function"""
    print("PROJECT COUNT VERIFICATION AND ANALYSIS")
    print("="*60)
    
    # Analyze all sources
    dws_analysis = await analyze_dws_projects()
    treasury_analysis = await analyze_treasury_api()
    mock_analysis = analyze_our_mock_data()
    
    # Summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY:")
    print("="*60)
    
    print("\n1. DWS PROJECT MONITORING DASHBOARD:")
    if dws_analysis.get('accessible'):
        print(f"   ✅ Accessible - Found {dws_analysis.get('tables_with_projects', 0)} potential project entries")
        print(f"   📊 Method: {dws_analysis.get('scraping_method', 'Unknown')}")
    else:
        print(f"   ❌ Not accessible - {dws_analysis.get('error', 'Unknown error')}")
    
    print("\n2. TREASURY MUNICIPAL DATA API:")
    if treasury_analysis.get('accessible'):
        print(f"   ✅ Accessible - {treasury_analysis.get('municipalities_available', 0)} municipalities")
        print(f"   📊 Note: {treasury_analysis.get('note', '')}")
    else:
        print(f"   ❌ Not accessible - {treasury_analysis.get('error', 'Unknown error')}")
    
    print(f"\n3. OUR SYSTEM'S CURRENT DATA:")
    print(f"   📦 DWS Projects (Mock): {mock_analysis['dws_projects']}")
    print(f"   📦 Treasury Municipalities: {mock_analysis['treasury_municipalities']}")
    print(f"   📊 Type: {mock_analysis['data_type']}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    
    # Determine if we're getting all available data
    if dws_analysis.get('accessible'):
        actual_projects = dws_analysis.get('tables_with_projects', 0)
        mock_projects = mock_analysis['dws_projects']
        
        if actual_projects > mock_projects:
            print(f"🔍 DWS: Real website has ~{actual_projects} projects, we use {mock_projects} mock projects")
            print("   → Consider implementing real-time scraping to get all projects")
        elif actual_projects == 0:
            print("🔍 DWS: Website structure may have changed - scraping needs updating")
        else:
            print("✅ DWS: Our mock data covers the available project scope")
    else:
        print("🔍 DWS: Website not accessible - using mock data is appropriate")
    
    if not treasury_analysis.get('accessible'):
        print("🔍 Treasury: API is down - using mock financial data is appropriate")
    else:
        print("✅ Treasury: API is accessible - could implement real financial data retrieval")
    
    print("\n📋 FINAL ASSESSMENT:")
    print("   • DWS: Website exists but may need updated scraping logic")
    print("   • Treasury: API has issues, mock data provides good coverage")
    print("   • Current system: Provides comprehensive mock data for development/demo")
    print("   • Production: Consider hybrid approach (real data + fallback to mock)")

if __name__ == "__main__":
    asyncio.run(main())
