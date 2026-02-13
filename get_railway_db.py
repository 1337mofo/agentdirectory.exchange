import requests
import json

# Railway API token
token = "a68b56c0-d254-43ed-8b4a-ef57b5d64059"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Query to get project and service IDs
query_projects = """
{
  me {
    id
    email
    projects {
      edges {
        node {
          id
          name
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
    }
  }
}
"""

print("=" * 60)
print("RAILWAY DATABASE_URL RETRIEVAL")
print("=" * 60)

# Get projects
response = requests.post(
    "https://backboard.railway.app/graphql",
    headers=headers,
    json={"query": query_projects}
)

print(f"\n[API Response Status]: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    if "errors" in data:
        print(f"\n[ERROR] GraphQL errors: {data['errors']}")
    else:
        print(f"\n[SUCCESS] Retrieved project data")
        print(json.dumps(data, indent=2))
        
        # Look for agentdirectoryexchange project
        projects = data.get("data", {}).get("me", {}).get("projects", {}).get("edges", [])
        
        for project_edge in projects:
            project = project_edge.get("node", {})
            if "agentdirectory" in project.get("name", "").lower():
                print(f"\n[FOUND] Project: {project['name']}")
                print(f"[ID] {project['id']}")
                
                # Look for PostgreSQL service
                services = project.get("services", {}).get("edges", [])
                for service_edge in services:
                    service = service_edge.get("node", {})
                    print(f"  - Service: {service['name']} (ID: {service['id']})")
else:
    print(f"\n[ERROR] API request failed: {response.text}")

print("\n" + "=" * 60)
