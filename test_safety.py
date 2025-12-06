import google.generativeai as genai
import os
from google.generativeai.types import HarmCategory, HarmBlockThreshold

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
        
        print("--- Testing Gemini 2.0 Flash Exp with Safety Settings ---")
        # Trying the experimental model which might have different capabilities/rules
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        try:
            print("Sending request...")
            # Explicitly asking for image generation in the prompt
            response = model.generate_content(
                "Generate an image of a crochet granny square.", 
                safety_settings=safety_settings
            )
            print("Response received.")
            
            if response.parts:
                print(f"Parts: {len(response.parts)}")
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print("SUCCESS: Image generated (Inline Data)!")
                    if hasattr(part, 'text'):
                        print(f"Text: {part.text}")
            else:
                print("No parts.")
                print(response.text)

        except Exception as e:
            print(f"Error: {e}")

except Exception as e:
    print(f"Error: {e}")
