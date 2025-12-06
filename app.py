import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
import io
import urllib.parse

import os
import smtplib
import ssl
from email.message import EmailMessage
from PIL import Image

# --- Configuration & Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)
icon_path_png = os.path.join(current_dir, "icon.png")
icon_path_jpg = os.path.join(current_dir, "icon.jpg")

icon = None
if os.path.exists(icon_path_png):
    icon = Image.open(icon_path_png)
elif os.path.exists(icon_path_jpg):
    icon = Image.open(icon_path_jpg)

if icon is None:
    icon = "🧶"

# Debug output for user visibility
# st.write(f"Debug Path: {current_dir}")
# st.write(f"Icon Loaded: {icon != '🧶'}")

st.set_page_config(
    page_title="Custom Crochet Order Visualizer",
    page_icon=icon,
    layout="centered"
)

# Debug output (Temporary)
st.sidebar.text(f"Debug: Icon Loaded? {icon != '🧶'}")
st.sidebar.text(f"Path: {current_dir}")

# Requirements:
# streamlit
# google-generativeai
# st-gsheets-connection
# pandas
# requests

# Initialize Session State
if "generated_image" not in st.session_state:
    st.session_state.generated_image = None
if "generated_description" not in st.session_state:
    st.session_state.generated_description = None
if "form_inputs" not in st.session_state:
    st.session_state.form_inputs = {}

# --- API Setup ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("Missing GEMINI_API_KEY in .streamlit/secrets.toml")
        st.stop()
except Exception as e:
    st.error(f"Error configuring API: {e}")
    st.stop()

# --- Helper Functions ---


@st.cache_data(show_spinner=False)
def generate_image_prompt(inputs):
    """
    Uses Gemini 2.0 Flash to translate user inputs into a visual prompt.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Dynamic Measurements Construction
        measurements_str = ""
        if inputs.get('measurements_bust'):
            measurements_str += f"Bust: {inputs['measurements_bust']}cm, "
        if inputs.get('measurements_waist'):
            measurements_str += f"Waist: {inputs['measurements_waist']}cm, "
        if inputs.get('measurements_hip'):
            measurements_str += f"Hip: {inputs['measurements_hip']}cm, "
        if inputs.get('measurements_length'):
            # Context-aware label for prompt
            label = "Height" if inputs['category'] == "Stuffed Animals" else "Length"
            measurements_str += f"{label}: {inputs['measurements_length']}cm, "
        if inputs.get('measurements_width'):
             measurements_str += f"Width: {inputs['measurements_width']}cm, "

        # Remove trailing comma
        measurements_str = measurements_str.rstrip(", ")

        prompt = f"""
        You are an expert Crochet Designer and AI Prompt Engineer.
        Your task is to take the following user specifications for a crochet item and convert them into a highly descriptive, photorealistic image generation prompt for an AI model.
        
        User Inputs:
        - Category: {inputs['category']}
        - Item Name: {inputs['item_name']}
        - Measurements/Size: {measurements_str}
        - Embellishments: {inputs['embellishment_types']}
        - Color Palette: {inputs['colors']}
        - Vibe/Style: {inputs['style']}
        
        Constraints & Requirements:
        - Emphasize textures: Mention specific stitches (e.g., waffle stitch, granny squares, ribbing), yarn types (e.g., chunky wool, soft acrylic halo, cotton), and craftsmanship.
        - Translate measurements into visual proportions (e.g., "cropped length," "oversized sleeves," "knee-length").
        - CRITICAL: Use the "Embellishments" input to make sure the specific embellishment (e.g. Pearls, Ruffles) is clearly visible and features prominently in the design. If the user selected an embellishment, you MUST describe how it is applied to the item.
        - The output should be a single, cohesive paragraph describing the visual appearance of the item, ensuring the entire item is visible with no clipping of the image.
        - The item MUST be shown from a direct front view, facing forward towards the camera.
        - Do NOT include markdown formatting or introductory text. Just the prompt.
        """

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating prompt with Gemini: {e}")
        return None


@st.cache_data(show_spinner=False)
def generate_image(prompt, embellishments=None):
    """
    Uses Pollinations.ai to generate an image from the prompt (Free, no API key required).
    """
    try:
        # Pollinations uses a simple URL structure.
        # We encode the prompt to ensure URL safety.
        encoded_prompt = urllib.parse.quote(prompt)

        # Adding nologo=true to remove the watermark if possible, though it's a free service.
        # Enhancing prompt slightly for better results with Pollinations (Stable Diffusion based)
        base_prompt = f"{encoded_prompt}, photorealistic, 8k, crochet texture, centered, full front view, facing camera"

        if embellishments and embellishments.lower() != "none":
            base_prompt += f", adorned with {embellishments}, {embellishments} details"

        final_prompt = base_prompt

        url = f"https://image.pollinations.ai/prompt/{final_prompt}?nologo=true"

        response = requests.get(url)

        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            st.error(
                f"Image generation failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None


def save_order(data):
    """
    Saves the order to Google Sheets.
    """
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Fetch existing data to append
        # Fetch existing data to append
        existing_data = conn.read(worksheet="Orders", ttl=5)

        # If sheet is empty, create a new dataframe
        if existing_data is None:
            existing_data = pd.DataFrame()

        updated_df = pd.concat([existing_data, data], ignore_index=True)

        conn.update(data=updated_df, worksheet="Orders")
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False


def send_email(subject, message_body, user_email):
    """
    Sends an email to the business address using credentials from secrets.toml.
    """
    try:
        # Check for credentials
        if "email" not in st.secrets:
            st.warning(
                "Email configuration missing in .streamlit/secrets.toml. Email not sent.")
            # For testing, we just return True to verify UI flow
            return True

        email_config = st.secrets["email"]
        smtp_server = email_config["smtp_server"]
        smtp_port = email_config["smtp_port"]
        sender_email = email_config["sender_email"]
        password = email_config["password"]
        receiver_email = email_config["receiver_email"]

        # Create message
        msg = EmailMessage()
        msg["Subject"] = f"New Inquiry: {subject}"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        # Content
        full_content = f"""
        New Message from CozyCrafts App:
        
        From: {user_email}
        Subject: {subject}
        
        Message:
        {message_body}
        """
        msg.set_content(full_content)

        # Send
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False


@st.dialog("Contact Designer")
def contact_form():
    st.write("Have a question or custom request? Send me a message!")

    with st.form("contact_form"):
        user_email = st.text_input("Your Email")
        subject = st.text_input("Subject")
        message = st.text_area("Message")

        submit = st.form_submit_button("Send Message")

        if submit:
            if not user_email or not subject or not message:
                st.error("Please fill in all fields.")
            else:
                if send_email(subject, message, user_email):
                    st.success(
                        "Message sent successfully! I'll get back to you shortly.")
                    time.sleep(2)
                    st.rerun()

# --- UI Layout ---

# 1. Title Layout (Responsive to Icon Type)
if isinstance(icon, str):
    st.title(f"{icon} Custom Crochet Order Visualizer")
else:
    # Centered Image Layout
    col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
    with col2:
        st.image(icon, width="stretch")

st.markdown("Design your dream crochet piece and see it come to life with AI!")

if st.button("📧 Contact Designer"):
    contact_form()

# 1. Input Form
with st.container():
    st.subheader("1. Design Your Item")

    col1, col2 = st.columns(2)

    with col1:
        item_name = st.text_input(
            "Specific Item Name", placeholder="e.g., Granny Square Cardigan")
        category = st.selectbox(
            "Item Category",
            ["Dresses", "Tops", "Bottoms", "Lingerie",
                "Pyjamas", "Blankets", "Stuffed Animals"]
        )
        style = st.selectbox(
            "Fabric Types",
            ["Cotton", "Silk", "Linen", "Patterned"]
        )
        colors = st.text_input(
            "Color Palette", placeholder="e.g., Sage Green, Cream, and Dusty Rose")
        embellishment_types = st.selectbox(
            "Embellishment Types",
            ["None", "Buttons", "Ruffles", "Lace", "Beading", "Pearls"]
        )

    with col2:
        # Measurement Logic Configuration
        # Default to all if not specified (safe fallback)
        category_config = {
            "Dresses": ["Bust", "Waist", "Hip", "Length"],
            "Tops": ["Bust", "Waist", "Length"],
            "Bottoms": ["Waist", "Hip", "Length"],
            "Lingerie": ["Bust", "Waist", "Hip"],
            "Pyjamas": ["Bust", "Waist", "Hip", "Length"],
            "Blankets": ["Length", "Width"],
            "Stuffed Animals": ["Height"]  # We will map "Height" to the Length variable logic
        }

        # Determine which measurements to show based on category
        active_measurements = category_config.get(category, ["Length"])

        measurements_bust = None
        measurements_waist = None
        measurements_hip = None
        measurements_length = None
        measurements_width = None

        if "Bust" in active_measurements:
            measurements_bust = st.slider(
                "Bust Measurement (cm)",
                min_value=20, max_value=180, value=70,
                help="Slide to adjust the bust size."
            )
        
        if "Waist" in active_measurements:
            measurements_waist = st.slider(
                "Waist Measurement (cm)",
                min_value=20, max_value=180, value=70,
                help="Slide to adjust the waist size."
            )
            
        if "Hip" in active_measurements:
            measurements_hip = st.slider(
                "Hip Measurement (cm)",
                min_value=20, max_value=180, value=70,
                help="Slide to adjust the hip size."
            )

        # "Length" and "Height" both use the measurements_length variable, just different label
        if "Length" in active_measurements:
            measurements_length = st.slider(
                "Length (cm)",
                min_value=10, max_value=250, value=60,
                help="Slide to adjust the length."
            )
        elif "Height" in active_measurements:
            measurements_length = st.slider(
                "Height (cm)",
                min_value=5, max_value=100, value=30,
                help="Slide to adjust the height of the stuffed animal."
            )

        if "Width" in active_measurements:
            measurements_width = st.slider(
                "Width (cm)",
                min_value=10, max_value=250, value=100,
                help="Slide to adjust the width."
            )

    generate_btn = st.button("Generate Preview", type="primary")
    st.info("Generating Images Can Take Some Time. Please Be Patient.")
    st.caption("**Please note that the generated image is a preview and may not be an exact representation of the final product.**")

# 2. Logic for Generation
if generate_btn:
    if not item_name or not colors:
        st.warning(
            "Please fill in all fields (Item Name, Colors) to generate a preview.")
    else:
        with st.spinner("Consulting the AI Crochet Designer... (Generating Prompt)"):
            # Store inputs in session state
            st.session_state.form_inputs = {
                "category": category,
                "embellishment_types": embellishment_types,
                "item_name": item_name,
                "measurements_bust": measurements_bust,
                "measurements_waist": measurements_waist,
                "measurements_hip": measurements_hip,
                "measurements_length": measurements_length,
                "measurements_width": measurements_width,
                "colors": colors,
                "style": style
            }

            # Step 2: Translation Layer
            visual_prompt = generate_image_prompt(st.session_state.form_inputs)

            if visual_prompt:
                st.session_state.generated_description = visual_prompt

                with st.spinner("Weaving pixels... (Generating Image)"):
                    # Step 3: Visualization Layer
                    image = generate_image(
                        visual_prompt, st.session_state.form_inputs.get('embellishment_types'))

                    if image:
                        st.session_state.generated_image = image
                    else:
                        st.error("Failed to generate image. Please try again.")

# 3. Display Results
if st.session_state.generated_image:
    st.divider()
    st.subheader("2. Preview & Confirmation")

    st.image(st.session_state.generated_image,
             caption="AI Generated Preview", width="stretch")

    with st.expander("See AI Interpretation (Visual Prompt)"):
        st.write(st.session_state.generated_description)

    # 4. Order Submission
    st.markdown("### Love it? Place your order!")
    with st.form("confirm_order_form"):
        user_name = st.text_input("Your Name")
        user_email = st.text_input("Your Email")

        submit_order = st.form_submit_button("Confirm & Submit Order")

        if submit_order:
            if not user_name or not user_email:
                st.warning(
                    "Please provide your name and email to place the order.")
            else:
                # Prepare data
                order_data = pd.DataFrame([{
                    "Status": "New Order",
                    "Timestamp": pd.Timestamp.now(),
                    "User Name": user_name,
                    "User Email": user_email,
                    "Category": st.session_state.form_inputs['category'],
                    "Item Name": st.session_state.form_inputs['item_name'],
                    "Bust (cm)": st.session_state.form_inputs.get('measurements_bust'),
                    "Waist (cm)": st.session_state.form_inputs.get('measurements_waist'),
                    "Hip (cm)": st.session_state.form_inputs.get('measurements_hip'),
                    "Length (cm)": st.session_state.form_inputs.get('measurements_length'),
                    "Width (cm)": st.session_state.form_inputs.get('measurements_width'),
                    "Embellishments": st.session_state.form_inputs['embellishment_types'],
                    "Colors": st.session_state.form_inputs['colors'],
                    "Style": st.session_state.form_inputs['style'],
                    "AI Description": st.session_state.generated_description,

                }])

                # Save to Sheets
                if save_order(order_data):
                    st.success(
                        "Order placed successfully! We'll be in touch soon.")
                    st.balloons()
