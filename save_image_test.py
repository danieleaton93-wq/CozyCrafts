import google.generativeai as genai
import os
import PIL.Image
import io

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
        
        print("--- Saving Image from Gemini 2.0 Flash ---")
        model = genai.GenerativeModel("gemini-2.0-flash")
        try:
            response = model.generate_content("Generate an image of a handcrafted crochet cardigan on a mannequin.")
            
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    print("Found inline data!")
                    img_data = part.inline_data.data
                    img = PIL.Image.open(io.BytesIO(img_data))
                    img.save("test_bear.png")
                    print("Saved test_bear.png")
                    break
            else:
                print("No image found in response.")
                print(response.text)

        except Exception as e:
            print(f"Error: {e}")

except Exception as e:
    print(f"Error: {e}")
