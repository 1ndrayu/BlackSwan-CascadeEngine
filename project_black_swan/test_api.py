import requests
import json

url = "http://localhost:6001/api/simulate"
payload = {
    "densities": "2.0",
    "dimension_scales": "100",
    "regions": "20",
    "scenarios": "10",
    "time_units": "12",
    "num_nodes": "1000",
    "initial_shock": "1000000"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Received labels and datasets.")
        print(f"Labels count: {len(data.get('labels', []))}")
        print(f"Datasets count: {len(data.get('datasets', []))}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Failed to connect: {e}")
