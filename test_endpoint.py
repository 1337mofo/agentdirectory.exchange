#!/usr/bin/env python3
import requests
import time

print("Testing agentdirectory.exchange...")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

try:
    response = requests.get("https://agentdirectory.exchange/", timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response time: {response.elapsed.total_seconds():.2f}s")
    print(f"\nContent:")
    print(response.text[:500])
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 10 seconds")
except requests.exceptions.ConnectionError as e:
    print(f"ERROR: Connection failed - {e}")
except Exception as e:
    print(f"ERROR: {e}")
