#!/usr/bin/env python3
"""
Test data parsing and API responses for frontend consumption
"""
import asyncio
import httpx
import json

async def test_api_endpoints():
    """Test all key API endpoints for frontend consumption"""
    
    base_url = "http://localhost:8000/api/v1"
    
    endpoints = [
        "/health",
        "/etl/status", 
        "/projects?limit=3",
        "/municipalities?limit=3",
        "/reports/summary",
        "/etl/jobs"
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            try:
                print(f"\n{'='*60}")
                print(f"Testing: {base_url}{endpoint}")
                print('='*60)
                
                response = await client.get(f"{base_url}{endpoint}")
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            print(f"Response type: List with {len(data)} items")
                            print("First item structure:")
                            print(json.dumps(data[0], indent=2, default=str)[:500] + "...")
                        elif isinstance(data, dict):
                            print("Response type: Dictionary")
                            print("Keys:", list(data.keys()))
                            print("Sample data:")
                            print(json.dumps(data, indent=2, default=str)[:500] + "...")
                        else:
                            print(f"Response type: {type(data)}")
                            print(str(data)[:200] + "...")
                    except Exception as e:
                        print(f"JSON parsing error: {e}")
                        print("Raw response:", response.text[:200] + "...")
                else:
                    print(f"Error response: {response.text}")
                    
            except Exception as e:
                print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
