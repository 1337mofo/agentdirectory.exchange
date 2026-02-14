"""
Check environment variables in Railway for agentdirectory.exchange service
"""

import requests
import json

# Railway API configuration
RAILWAY_API_TOKEN = "a9cd7a25-7bb1-487b-9e86-3a7575a5703c"
PROJECT_ID = "df459949-3d36-4601-afcc-e50869c28223"
SERVICE_ID = "8b616d95-bf4b-43a2-a441-310f98a9ac82"  # agentdirectory.exchange
ENVIRONMENT_ID = "8c2d2a68-c760-4a39-b5bf-9c53e4900d0f"  # production
GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"

headers = {
    "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
    "Content-Type": "application/json"
}

# Query to get all variables
get_variables_query = """
query GetVariables($projectId: String!, $environmentId: String!, $serviceId: String!) {
  variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId) {
    edges {
      node {
        name
        value
      }
    }
  }
}
"""

print("Fetching environment variables for agentdirectory.exchange...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": get_variables_query,
        "variables": {
            "projectId": PROJECT_ID,
            "environmentId": ENVIRONMENT_ID,
            "serviceId": SERVICE_ID
        }
    }
)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

if "errors" in data:
    print(f"GraphQL errors: {data['errors']}")
    exit(1)

variables = data["data"]["variables"]["edges"]

print(f"\nFound {len(variables)} environment variables:\n")

for var in variables:
    name = var["node"]["name"]
    value = var["node"]["value"]
    
    # Truncate long values
    if len(value) > 80:
        display_value = value[:77] + "..."
    else:
        display_value = value
    
    print(f"  {name}: {display_value}")
    
    # Check DATABASE_URL specifically
    if name == "DATABASE_URL":
        if "mainline.proxy.rlwy.net:11716" in value:
            print(f"\n[OK] DATABASE_URL is set to Postgres-EmQ4!")
        elif "yamabiko" in value:
            print(f"\n[ERROR] DATABASE_URL still points to old yamabiko database!")
        else:
            print(f"\n[WARN] DATABASE_URL set but unknown database")

print("\n")
