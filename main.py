import streamlit as st
import requests
import wikipedia
import base64
import os
from wikipedia import DisambiguationError, PageError

# 🧾 Page setup
st.set_page_config(page_title="Griffin",
                   page_icon="🤖🤖", layout="centered")

# 🎨 Fonts (subtle professional look)
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)


def generate_svg_background(width=1920, height=1080):
    """
    Generate a professional SVG gradient background with subtle shapes and grain.
    Returns base64-encoded SVG (utf-8).
    """
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#0f172a"/>
          <stop offset="45%" stop-color="#0b3a57"/>
          <stop offset="100%" stop-color="#06202a"/>
        </linearGradient>
        <filter id="grain">
          <feTurbulence baseFrequency="0.8" numOctaves="2" stitchTiles="stitch"/>
          <feColorMatrix type="saturate" values="0"/>
          <feBlend mode="overlay"/>
        </filter>
        <filter id="soft">
          <feGaussianBlur stdDeviation="80"/>
        </filter>
      </defs>

      <rect width="100%" height="100%" fill="url(#bg)"/>

      <!-- Soft glow shapes -->
      <g opacity="0.08" fill="#ffffff">
        <ellipse cx="1600" cy="120" rx="420" ry="200" filter="url(#soft)"/>
        <ellipse cx="220" cy="860" rx="520" ry="260" filter="url(#soft)"/>
      </g>

      <!-- Subtle diagonal light -->
      <g opacity="0.04" transform="rotate(-12 960 540)" fill="#ffffff">
        <rect x="-200" y="300" width="2400" height="120" rx="60"/>
      </g>

      <!-- Very subtle grain -->
      <rect width="100%" height="100%" filter="url(#grain)" opacity="0.02"/>
    </svg>
    """
    return base64.b64encode(svg.encode("utf-8")).decode("utf-8")


def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def set_background(image_path: str | None = None):
    """
    Use a provided local image (PNG/JPG) if available, else fall back to generated SVG.
    The function writes a small CSS block to Streamlit to set the app background.
    """
    use_svg = True
    encoded = ""
    mime = "image/svg+xml"

    if image_path:
        try:
            if os.path.isfile(image_path) and os.access(image_path, os.R_OK):
                # Use the actual image bytes (keep original mime as png/jpg)
                with open(image_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                # Infer mime from extension
                ext = os.path.splitext(image_path)[1].lower()
                if ext in (".jpg", ".jpeg"):
                    mime = "image/jpeg"
                elif ext == ".png":
                    mime = "image/png"
                else:
                    mime = "image/png"
                use_svg = False
            else:
                # fallback to generated svg
                encoded = generate_svg_background()
                mime = "image/svg+xml"
                use_svg = True
        except Exception:
            encoded = generate_svg_background()
            mime = "image/svg+xml"
            use_svg = True
    else:
        encoded = generate_svg_background()
        mime = "image/svg+xml"
        use_svg = True

    # Safety: ensure CSS uses background-color fallback and centered content
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:{mime};base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
            min-height: 100vh;
            /* subtle overlay so content remains readable */
        }}
        /* Provide a semi-opaque container for main content to improve readability */
        .stApp > main {{
            background: linear-gradient(rgba(255,255,255,0.02), rgba(255,255,255,0.02));
            padding: 32px;
            border-radius: 12px;
        }}
        </style>
    """, unsafe_allow_html=True)


# Use generated SVG background by default; if you want to use a local image, pass its path:
set_background(image_path=None)

# 🔍 DuckDuckGo Instant Answer with fallback
def duckduckgo_search(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1&skip_disambig=1"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        if response.status_code != 200:
            return f"DuckDuckGo error: Status {response.status_code}"
        data = response.json()
        abstract = data.get("Abstract")
        if abstract:
            return abstract
        topics = data.get("RelatedTopics", [])
        for topic in topics:
            if isinstance(topic, dict) and "Text" in topic:
                return topic["Text"]
        return "DuckDuckGo found no summary for this query."
    except Exception as e:
        return f"DuckDuckGo error: {e}"

# 🌦️ Open-Meteo Weather
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        response = requests.get(url, timeout=6)
        data = response.json()
        weather = data.get("current_weather", {})
        return f"Temperature: {weather.get('temperature')}°C, Windspeed: {weather.get('windspeed')} km/h"
    except Exception as e:
        return f"Weather error: {e}"

# 📚 Wikipedia Summary with fallback
def wiki_summary(topic):
    try:
        cleaned = topic.lower().replace("what is", "").replace("who is", "").strip()
        results = wikipedia.search(cleaned)
        if results:
            try:
                return wikipedia.summary(results[0], sentences=3)
            except DisambiguationError as d:
                # pick first non-conflicting option if available
                try:
                    choice = d.options[0]
                    return wikipedia.summary(choice, sentences=2)
                except Exception:
                    return "Wikipedia: topic is ambiguous. Try a more specific query."
            except PageError:
                return "Wikipedia: page not found for the matched title."
        else:
            return "Wikipedia found no matching pages."
    except Exception as e:
        return f"Wikipedia error: {e}"

# 🧾 Custom CSS for a clean, professional look
st.markdown("""
    <style>
    body, .stApp, .css-1d391kg { font-family: 'Inter', sans-serif; }
    .title {
        font-size: 42px;
        font-weight: 700;
        color: #e6eef6;
        text-shadow: 1px 1px 8px rgba(0,0,0,0.6);
        text-align: center;
        margin-bottom: 8px;
    }
    .prompt {
        font-size: 20px;
        color: #dbe8f5;
        text-align: center;
        margin-bottom: 18px;
        letter-spacing: 0.2px;
    }
    .response {
        font-size: 16px;
        color: #041827;
        background-color: rgba(255,255,255,0.9);
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(2,6,23,0.25);
    }
    label[for="🔮 Your magical query:"] {
        font-size: 16px;
        color: #e6eef6;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


# 🧙‍♂️ Title and prompt
st.markdown('<div class="title">The Griffin</div>', unsafe_allow_html=True)
st.markdown('<div class="prompt">Bring forth your curiosity, young witch or wizard...</div>', unsafe_allow_html=True)

# 🧙‍♂️ Input and response
user_input = st.text_input("🔮 Your magical query:")

if user_input:
    # 🎵 Sound effect (optional)
    st.markdown("""
        <audio autoplay>
            <source src="https://www.soundjay.com/magic/magic-chime-01.mp3" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)

    # 📚 Wikipedia
    wiki_result = wiki_summary(user_input)
    st.markdown(
        f'<div class="response">📚 <b>Wikipedia says:</b> {wiki_result}</div>', unsafe_allow_html=True)

    # 🔍 DuckDuckGo
    duck_result = duckduckgo_search(user_input)
    st.markdown(
        f'<div class="response">🔍 <b>DuckDuckGo says:</b> {duck_result}</div>', unsafe_allow_html=True)

    # 🌦️ Weather (if location matches)
    location_coords = {
        "pithoragarh": (29.58, 80.22),
        "delhi": (28.61, 77.23),
        "london": (51.51, -0.13),
        "new york": (40.71, -74.01)
    }

    if user_input.lower() in location_coords:
        lat, lon = location_coords[user_input.lower()]
        weather_result = get_weather(lat, lon)
        st.markdown(
            f'<div class="response">🌦️ <b>Weather in {user_input.title()}:</b> {weather_result}</div>', unsafe_allow_html=True)
