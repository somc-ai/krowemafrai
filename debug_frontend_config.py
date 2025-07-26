#!/usr/bin/env python3
"""
Debug script to test frontend configuration
"""
import os
import requests
import json

def test_backend_urls():
    """Test different backend URLs to see which ones work"""
    urls_to_test = [
        "https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io",
        "https://backend-aiagents-gov.westeurope-01.azurecontainerapps.io",
        "https://backend-aiagents-gov.westeurope.azurecontainerapps.io"
    ]
    
    for url in urls_to_test:
        try:
            print(f"\n🧪 Testing: {url}")
            
            # Test health endpoint
            health_response = requests.get(f"{url}/health", timeout=10)
            print(f"   Health endpoint: {health_response.status_code}")
            
            # Test agent-tools endpoint
            agents_response = requests.get(f"{url}/api/agent-tools", timeout=10)
            print(f"   Agent-tools endpoint: {agents_response.status_code}")
            if agents_response.status_code == 200:
                agents_data = agents_response.json()
                print(f"   Found {len(agents_data)} agents")
                
            # Test input_task endpoint with a simple POST
            test_payload = {
                "session_id": "debug_test",
                "description": "This is a test scenario for debugging"
            }
            task_response = requests.post(
                f"{url}/api/input_task", 
                json=test_payload, 
                timeout=30
            )
            print(f"   Input-task endpoint: {task_response.status_code}")
            
            if agents_response.status_code == 200:
                print(f"   ✅ URL {url} is working!")
            else:
                print(f"   ❌ URL {url} has issues")
                
        except Exception as e:
            print(f"   ❌ Error testing {url}: {e}")

def test_frontend_config():
    """Test frontend config endpoint"""
    print("\n🔧 Testing frontend configuration...")
    
    # Check environment variables
    backend_url = os.getenv("BACKEND_API_URL", "NOT_SET")
    auth_enabled = os.getenv("AUTH_ENABLED", "NOT_SET")
    
    print(f"BACKEND_API_URL env var: {backend_url}")
    print(f"AUTH_ENABLED env var: {auth_enabled}")
    
    # Test what the /config endpoint would return
    from src.frontend.frontend_server import get_config
    import asyncio
    
    async def test_config():
        config = await get_config()
        print(f"Config endpoint would return: {json.dumps(config, indent=2)}")
    
    try:
        asyncio.run(test_config())
    except Exception as e:
        print(f"Error testing config: {e}")

if __name__ == "__main__":
    print("🔍 Frontend Configuration Debug Tool")
    print("=" * 50)
    
    test_backend_urls()
    test_frontend_config()
    
    print("\n" + "=" * 50)
    print("✨ Debug complete!")
