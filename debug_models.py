import google.generativeai as genai
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

    if not api_key:
        print("Could not find GEMINI_API_KEY")
    else:
        genai.configure(api_key=api_key)
        
        print("Listing Imagen models...")
        for m in genai.list_models():
            if "imagen" in m.name:
                print(f"{m.name} - Methods: {m.supported_generation_methods}")

except Exception as e:
    print(f"Error: {e}")
