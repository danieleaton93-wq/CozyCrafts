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
        
        print("--- Testing Gemini 2.0 Flash for Image Generation ---")
        model = genai.GenerativeModel("gemini-2.0-flash")
        try:
            response = model.generate_content("Generate an image of a crochet granny square.", generation_config={"response_mime_type": "image/jpeg"})
            print("Response received.")
            print(response)
            if response.parts:
                print(f"Parts: {len(response.parts)}")
                print(response.parts[0])
        except Exception as e:
            print(f"Gemini 2.0 Flash Error: {e}")

except Exception as e:
    print(f"Error: {e}")
