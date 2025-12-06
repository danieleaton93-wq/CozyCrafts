import requests
import json
import os

api_key = None
try:
    with open(".streamlit/secrets.toml", "r") as f:
        for line in f:
            if "GEMINI_API_KEY" in line:
                parts = line.split('=')
                if len(parts) > 1:
                    raw_key = parts[1].strip()
                    api_key = raw_key.strip('"').strip("'")
                    break
except Exception as e:
    print(f"Error reading secrets: {e}")

if not api_key:
    print("Could not find GEMINI_API_KEY")
else:
    print("--- Testing Imagen 4.0 REST API ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    data = {
        "instances": [
            {"prompt": "A cute crochet bear"}
        ],
        "parameters": {
            "sampleCount": 1
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if "predictions" in result:
                print("Success! Predictions found.")
                # print(result["predictions"][0].keys()) # Check keys
            else:
                print("No predictions in response.")
                print(result)
        else:
            print("Error response:")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")
