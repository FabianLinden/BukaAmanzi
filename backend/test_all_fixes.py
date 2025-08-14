#!/usr/bin/env python3
"""
Comprehensive test of all fixes applied to the BukaAmanzi application
"""
import asyncio
import httpx
import json

async def test_all_endpoints():
    """Test all fixed endpoints and validate data quality"""
    
    base_url = "http://localhost:8000/api/v1"
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                test_results["tests"].append({
                    "name": "Health Endpoint",
                    "status": "PASS",
                    "details": f"Service: {data.get('service')}, Status: {data.get('status')}"
                })
                test_results["passed"] += 1
            else:
                test_results["tests"].append({
                    "name": "Health Endpoint", 
                    "status": "FAIL",
                    "details": f"Status: {response.status_code}"
                })
                test_results["failed"] += 1
        except Exception as e:
            test_results["tests"].append({
                "name": "Health Endpoint",
                "status": "FAIL", 
                "details": f"Error: {str(e)}"
            })
            test_results["failed"] += 1
        
        # Test 2: Detailed Health endpoint
        try:
            response = await client.get(f"{base_url}/health/detailed")
            if response.status_code == 200:
                data = response.json()
                test_results["tests"].append({
                    "name": "Detailed Health Endpoint",
                    "status": "PASS",
                    "details": f"Projects: {data['database']['total_projects']}, Municipalities: {data['database']['total_municipalities']}"
                })
                test_results["passed"] += 1
            else:
                test_results["tests"].append({
                    "name": "Detailed Health Endpoint",
                    "status": "FAIL",
                    "details": f"Status: {response.status_code}"
                })
                test_results["failed"] += 1
        except Exception as e:
            test_results["tests"].append({
                "name": "Detailed Health Endpoint",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
            test_results["failed"] += 1
        
        # Test 3: Reports Summary endpoint
        try:
            response = await client.get(f"{base_url}/reports/summary")
            if response.status_code == 200:
                data = response.json()
                test_results["tests"].append({
                    "name": "Reports Summary Endpoint",
                    "status": "PASS",
                    "details": f"Projects: {data['system_overview']['total_projects']}, Budget: R{data['system_overview']['total_budget_allocated']:,.0f}"
                })
                test_results["passed"] += 1
            else:
                test_results["tests"].append({
                    "name": "Reports Summary Endpoint",
                    "status": "FAIL",
                    "details": f"Status: {response.status_code}"
                })
                test_results["failed"] += 1
        except Exception as e:
            test_results["tests"].append({
                "name": "Reports Summary Endpoint",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
            test_results["failed"] += 1
        
        # Test 4: Projects endpoint (check for redirects)
        try:
            response = await client.get(f"{base_url}/projects/")
            if response.status_code == 200:
                data = response.json()
                # Check data quality - look for cleaned names
                clean_names = all(
                    "All!ABCDEFGHIJKLMNOPQRSTUVWXYZ" not in project.get("name", "")
                    for project in data[:5]  # Check first 5 projects
                )
                test_results["tests"].append({
                    "name": "Projects Endpoint & Data Quality",
                    "status": "PASS" if clean_names else "PARTIAL",
                    "details": f"Count: {len(data)}, Clean names: {clean_names}"
                })
                test_results["passed"] += 1
            else:
                test_results["tests"].append({
                    "name": "Projects Endpoint",
                    "status": "FAIL",
                    "details": f"Status: {response.status_code}"
                })
                test_results["failed"] += 1
        except Exception as e:
            test_results["tests"].append({
                "name": "Projects Endpoint",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
            test_results["failed"] += 1
        
        # Test 5: Municipalities endpoint (check for redirects and data quality)
        try:
            response = await client.get(f"{base_url}/municipalities/")
            if response.status_code == 200:
                data = response.json()
                # Check data quality - look for cleaned names
                clean_names = all(
                    "All!ABCDEFGHIJKLMNOPQRSTUVWXYZ" not in municipality.get("name", "")
                    for municipality in data[:5]  # Check first 5 municipalities
                )
                test_results["tests"].append({
                    "name": "Municipalities Endpoint & Data Quality",
                    "status": "PASS" if clean_names else "PARTIAL",
                    "details": f"Count: {len(data)}, Clean names: {clean_names}"
                })
                test_results["passed"] += 1
            else:
                test_results["tests"].append({
                    "name": "Municipalities Endpoint",
                    "status": "FAIL",
                    "details": f"Status: {response.status_code}"
                })
                test_results["failed"] += 1
        except Exception as e:
            test_results["tests"].append({
                "name": "Municipalities Endpoint",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
            test_results["failed"] += 1
        
        # Test 6: ETL Status endpoint
        try:
            response = await client.get(f"{base_url}/etl/status")
            if response.status_code == 200:
                data = response.json()
                test_results["tests"].append({
                    "name": "ETL Status Endpoint",
                    "status": "PASS",
                    "details": f"Status: {data.get('status')}, Projects: {data.get('total_projects')}"
                })
                test_results["passed"] += 1
            else:
                test_results["tests"].append({
                    "name": "ETL Status Endpoint",
                    "status": "FAIL",
                    "details": f"Status: {response.status_code}"
                })
                test_results["failed"] += 1
        except Exception as e:
            test_results["tests"].append({
                "name": "ETL Status Endpoint",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
            test_results["failed"] += 1
    
    return test_results

async def main():
    print("🔧 COMPREHENSIVE TESTING OF ALL FIXES")
    print("="*60)
    
    results = await test_all_endpoints()
    
    print(f"\n📊 TEST RESULTS SUMMARY")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success Rate: {(results['passed'] / (results['passed'] + results['failed']) * 100):.1f}%")
    
    print(f"\n📋 DETAILED RESULTS")
    print("-" * 60)
    
    for test in results["tests"]:
        status_icon = "✅" if test["status"] == "PASS" else "⚠️" if test["status"] == "PARTIAL" else "❌"
        print(f"{status_icon} {test['name']}: {test['status']}")
        print(f"   {test['details']}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
