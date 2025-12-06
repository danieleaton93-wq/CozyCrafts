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
        
        print("--- Testing Gemini 2.0 Flash Simple Prompt ---")
        model = genai.GenerativeModel("gemini-2.0-flash")
        try:
            response = model.generate_content("Generate an image of a cute crochet bear.")
            print("Response received.")
            if response.parts:
                print(f"Parts: {len(response.parts)}")
                for part in response.parts:
                    print(f"Part type: {type(part)}")
                    if hasattr(part, 'text'):
                        print(f"Text: {part.text}")
                    if hasattr(part, 'image'):
                        print("Image found!")
                    if hasattr(part, 'inline_data'):
                        print("Inline data found!")
            else:
                print("No parts in response.")
                print(response.text)
                
        except Exception as e:
            print(f"Error: {e}")

except Exception as e:
    print(f"Error: {e}")
