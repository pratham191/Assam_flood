




import streamlit as st
import pandas as pd
import pickle
import os
import requests
import folium
from streamlit_folium import st_folium

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Assam Flood Prediction",
    page_icon="🌊",
    layout="centered"
)

OPENWEATHER_API_KEY = "6530f38d3899c3c1fde8cb37e5dbea33"

# ---------------- DISTRICT COORDINATES ----------------
district_coords = {
    "Guwahati": [26.1445, 91.7362],
    "Dibrugarh": [27.4728, 94.9120],
    "Jorhat": [26.7509, 94.2037],
    "Silchar": [24.8333, 92.7789],
    "Tezpur": [26.6528, 92.7926]
}

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    path = os.path.join("models", "assam_floodpkl")
    with open(path, "rb") as f:
        model = pickle.load(f)
    return model

model = load_model()

# ---------------- WEATHER FETCH FUNCTION ----------------
def fetch_weather(lat, lon):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    response = requests.get(url)
    data = response.json()

    rainfall = data.get("rain", {}).get("1h", 0.0)
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]

    return rainfall, temperature, humidity

# ---------------- UI ----------------
st.title("🌊 Assam Flood Prediction System")
st.markdown("Real-time flood prediction using **OpenWeather API + ML**")
st.divider()

district = st.selectbox("📍 Select District", list(district_coords.keys()))

water_level = st.number_input(
    "River Water Level (m)",
    min_value=0.0,
    step=0.1
)

if st.button("🚨 Predict Flood"):
    lat, lon = district_coords[district]

    # Fetch live weather
    rainfall, temperature, humidity = fetch_weather(lat, lon)

    st.info(
        f"""
        **Live Weather Data**
        - 🌧️ Rainfall: {rainfall} mm
        - 🌡️ Temperature: {temperature} °C
        - 💧 Humidity: {humidity} %
        """
    )

    # Prepare input for model
    input_data = pd.DataFrame(
        [[rainfall, water_level, temperature, humidity]],
        columns=["rainfall", "water_level", "temperature", "humidity"]
    )

    prediction = model.predict(input_data)[0]

    st.divider()

    # Result
    if prediction == 1:
        st.error("⚠️ Flood Alert: HIGH RISK")
        color = "red"
        status = "Flood Risk"
    else:
        st.success("✅ No Flood Expected")
        color = "green"
        status = "Safe"

    # ---------------- MAP ----------------
    m = folium.Map(location=[lat, lon], zoom_start=7)

    folium.CircleMarker(
        location=[lat, lon],
        radius=12,
        color=color,
        fill=True,
        fill_color=color,
        popup=f"{district}: {status}"
    ).add_to(m)

    st.subheader("🗺️ Flood Prediction Map")
    st_folium(m, width=700, height=450)

st.markdown("---")
st.caption("Assam Flood Prediction | OpenWeather API + ML")




