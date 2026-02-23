"""
Check Railway deployment logs
"""
import requests
import json

RAILWAY_API_TOKEN = "a9cd7a25-7bb1-487b-9e86-3a7575a5703c"
PROJECT_ID = "df459949-3d36-4601-afcc-e50869c28223"
SERVICE_ID = "8b616d95-bf4b-43a2-a441-310f98a9ac82"
ENVIRONMENT_ID = "8c2d2a68-c760-4a39-b5bf-9c53e4900d0f"
DEPLOYMENT_ID = "3354171c-fefd-40ca-9ef9-473aef4da8af"
GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"

headers = {
    "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
    "Content-Type": "application/json"
}

# Get deployment logs
logs_query = """
query GetLogs($deploymentId: String!, $limit: Int) {
  deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
    edges {
      node {
        message
        timestamp
      }
    }
  }
}
"""

print("[*] Fetching deployment logs...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    headers=headers,
    json={
        "query": logs_query,
        "variables": {
            "deploymentId": DEPLOYMENT_ID,
            "limit": 50
        }
    }
)

if response.status_code == 200:
    data = response.json()
    if "data" in data and "deploymentLogs" in data["data"]:
        logs = data["data"]["deploymentLogs"]["edges"]
        
        print(f"\n[OK] Found {len(logs)} log entries:\n")
        
        for log in reversed(logs[-20:]):  # Last 20 logs
            msg = log["node"]["message"].strip()
            if msg:
                print(msg)
    else:
        print("[ERROR] No logs found")
        print(json.dumps(data, indent=2))
else:
    print(f"[ERROR] HTTP {response.status_code}")
    print(response.text)
