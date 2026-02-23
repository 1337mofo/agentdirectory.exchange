"""
Trigger Railway deployment for agentdirectory.exchange
"""
import requests
import json
import time

RAILWAY_API_TOKEN = "a9cd7a25-7bb1-487b-9e86-3a7575a5703c"
PROJECT_ID = "df459949-3d36-4601-afcc-e50869c28223"
SERVICE_ID = "8b616d95-bf4b-43a2-a441-310f98a9ac82"  # agentdirectory.exchange
ENVIRONMENT_ID = "8c2d2a68-c760-4a39-b5bf-9c53e4900d0f"  # production
GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"

headers = {
    "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
    "Content-Type": "application/json"
}

# Check latest deployments
check_deployments_query = """
query GetDeployments($projectId: String!, $environmentId: String!) {
  deployments(input: {projectId: $projectId, environmentId: $environmentId}) {
    edges {
      node {
        id
        status
        createdAt
        suggestAddServiceDomain
        staticUrl
        serviceId
        meta
      }
    }
  }
}
"""

print("[*] Checking recent deployments...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": check_deployments_query,
        "variables": {
            "projectId": PROJECT_ID,
            "environmentId": ENVIRONMENT_ID
        }
    }
)

if response.status_code == 200:
    data = response.json()
    if "data" in data and "deployments" in data["data"]:
        deployments = data["data"]["deployments"]["edges"]
        
        # Filter for our service
        service_deployments = [d for d in deployments if d["node"]["serviceId"] == SERVICE_ID]
        
        if service_deployments:
            latest = service_deployments[0]["node"]
            print(f"[OK] Latest deployment: {latest['id']}")
            print(f"    Status: {latest['status']}")
            print(f"    Created: {latest['createdAt']}")
            
            if latest['status'] in ['BUILDING', 'DEPLOYING']:
                print("\n[INFO] Deployment already in progress - waiting for completion...")
                print("Railway auto-deploys from GitHub commits")
                exit(0)

# Trigger redeploy mutation
redeploy_mutation = """
mutation ServiceInstanceRedeploy($environmentId: String!, $serviceId: String!) {
  serviceInstanceRedeploy(environmentId: $environmentId, serviceId: $serviceId)
}
"""

print("\n[*] Triggering redeploy...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": redeploy_mutation,
        "variables": {
            "environmentId": ENVIRONMENT_ID,
            "serviceId": SERVICE_ID
        }
    }
)

if response.status_code == 200:
    data = response.json()
    if "errors" in data:
        print(f"[ERROR] GraphQL errors: {data['errors']}")
    else:
        print("[OK] Redeploy triggered successfully!")
        print("\n[*] Railway is rebuilding and deploying...")
        print("    Monitor at: https://railway.app/project/" + PROJECT_ID)
        print("\n[INFO] Deployment typically takes 2-3 minutes")
else:
    print(f"[ERROR] HTTP {response.status_code}: {response.text}")
