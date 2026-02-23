"""
Check Railway deployment status
"""
import requests
import json

RAILWAY_API_TOKEN = "a9cd7a25-7bb1-487b-9e86-3a7575a5703c"
PROJECT_ID = "df459949-3d36-4601-afcc-e50869c28223"
SERVICE_ID = "8b616d95-bf4b-43a2-a441-310f98a9ac82"
ENVIRONMENT_ID = "8c2d2a68-c760-4a39-b5bf-9c53e4900d0f"
GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"

headers = {
    "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
    "Content-Type": "application/json"
}

query = """
query GetDeployments($projectId: String!, $environmentId: String!) {
  deployments(input: {projectId: $projectId, environmentId: $environmentId}) {
    edges {
      node {
        id
        status
        createdAt
        serviceId
      }
    }
  }
}
"""

response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": query,
        "variables": {
            "projectId": PROJECT_ID,
            "environmentId": ENVIRONMENT_ID
        }
    }
)

if response.status_code == 200:
    data = response.json()
    deployments = data["data"]["deployments"]["edges"]
    
    # Filter for our service
    service_deployments = [d for d in deployments if d["node"]["serviceId"] == SERVICE_ID]
    
    if service_deployments:
        latest = service_deployments[0]["node"]
        status = latest['status']
        
        print(f"Deployment Status: {status}")
        print(f"Created: {latest['createdAt']}")
        print(f"ID: {latest['id']}")
        
        if status == "SUCCESS":
            print("\n[OK] Deployment successful!")
        elif status in ["BUILDING", "DEPLOYING"]:
            print("\n[WAIT] Deployment in progress...")
        elif status == "FAILED":
            print("\n[ERROR] Deployment failed!")
        else:
            print(f"\n[INFO] Status: {status}")
else:
    print(f"[ERROR] HTTP {response.status_code}")
