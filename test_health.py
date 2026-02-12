#!/usr/bin/env python3
import requests

endpoints = [
    "https://agentdirectory.exchange/health",
    "https://agentdirectory.exchange/",
    "https://agentdirectory.exchange/docs"
]

for url in endpoints:
    try:
        print(f"Testing: {url}")
        response = requests.get(url, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Time: {response.elapsed.total_seconds():.2f}s")
        print(f"  Content: {response.text[:200]}\n")
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT after 10s\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
