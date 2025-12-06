import requests
import io
from PIL import Image

def test_pollinations():
    prompt = "A cute handcrafted crochet bear, amigurumi style, soft lighting"
    # Pollinations URL - simple and free
    url = f"https://image.pollinations.ai/prompt/{prompt}"
    
    print(f"Requesting: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Success! Image received.")
        img = Image.open(io.BytesIO(response.content))
        img.save("pollinations_test.jpg")
        print("Saved pollinations_test.jpg")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_pollinations()
