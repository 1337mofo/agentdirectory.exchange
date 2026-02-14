"""
Set DATABASE_URL environment variable in Railway for agentdirectory.exchange service
Uses Railway GraphQL API
"""

import requests
import json

# Railway API configuration
RAILWAY_API_TOKEN = "a9cd7a25-7bb1-487b-9e86-3a7575a5703c"
PROJECT_ID = "df459949-3d36-4601-afcc-e50869c28223"
GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"

# New database URL (Postgres-EmQ4)
NEW_DATABASE_URL = "postgresql://postgres:aRFnDbaXZvAaIKFgFBnpjRmzoanlwGkO@mainline.proxy.rlwy.net:11716/railway"

headers = {
    "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Get service ID for agentdirectory.exchange
get_services_query = """
query GetServices($projectId: String!) {
  project(id: $projectId) {
    services {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""

print("Step 1: Getting service ID...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": get_services_query,
        "variables": {"projectId": PROJECT_ID}
    }
)

if response.status_code != 200:
    print(f"Error getting services: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
services = data["data"]["project"]["services"]["edges"]

print(f"Found {len(services)} services:")
for service in services:
    print(f"  - {service['node']['name']} (ID: {service['node']['id']})")

# Find agentdirectory.exchange service
service_id = None
for service in services:
    if "agentdirectory" in service["node"]["name"].lower():
        service_id = service["node"]["id"]
        service_name = service["node"]["name"]
        break

if not service_id:
    print("Error: Could not find agentdirectory.exchange service")
    exit(1)

print(f"\nUsing service: {service_name} (ID: {service_id})")

# Step 2: Get environment ID (production environment)
get_environments_query = """
query GetEnvironments($projectId: String!) {
  project(id: $projectId) {
    environments {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""

print("\nStep 2: Getting environment ID...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": get_environments_query,
        "variables": {"projectId": PROJECT_ID}
    }
)

if response.status_code != 200:
    print(f"Error getting environments: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
environments = data["data"]["project"]["environments"]["edges"]

print(f"Found {len(environments)} environments:")
for env in environments:
    print(f"  - {env['node']['name']} (ID: {env['node']['id']})")

# Use production environment (or first available)
environment_id = environments[0]["node"]["id"]
environment_name = environments[0]["node"]["name"]

print(f"\nUsing environment: {environment_name} (ID: {environment_id})")

# Step 3: Set DATABASE_URL variable
set_variable_mutation = """
mutation VariableUpsert($input: VariableUpsertInput!) {
  variableUpsert(input: $input)
}
"""

print("\nStep 3: Setting DATABASE_URL environment variable...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": set_variable_mutation,
        "variables": {
            "input": {
                "projectId": PROJECT_ID,
                "environmentId": environment_id,
                "serviceId": service_id,
                "name": "DATABASE_URL",
                "value": NEW_DATABASE_URL
            }
        }
    }
)

if response.status_code != 200:
    print(f"Error setting variable: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
if "errors" in result:
    print(f"GraphQL errors: {result['errors']}")
    exit(1)

print(f"\n[OK] SUCCESS: DATABASE_URL set to Postgres-EmQ4")
print(f"\nDatabase: mainline.proxy.rlwy.net:11716/railway")
print(f"\n[WARN]  Note: Railway will redeploy the service to apply environment variable changes")
print(f"   Deployment will complete in ~2-3 minutes")
