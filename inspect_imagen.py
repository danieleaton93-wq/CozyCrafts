import google.generativeai as genai
import inspect

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
        
        print("--- Inspecting GenerativeModel for Imagen ---")
        model = genai.GenerativeModel("imagen-4.0-generate-001")
        print(f"Model object type: {type(model)}")
        print("Dir of model object:")
        print(dir(model))
        
        print("\n--- Checking for generate_images in module ---")
        if hasattr(genai, 'generate_images'):
            print("genai.generate_images exists")
        else:
            print("genai.generate_images DOES NOT exist")

except Exception as e:
    print(f"Error: {e}")
