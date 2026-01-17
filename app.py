from streamlit_folium import st_folium
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Assam Flood Prediction System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENWEATHER_API_KEY = "6530f38d3899c3c1fde8cb37e5dbea33"

# ---------------- EXTENDED DISTRICT DATA ----------------
district_data = {
    "Guwahati": {"coords": [26.1445, 91.7362], "river": "Brahmaputra", "danger_level": 50.5},
    "Dibrugarh": {"coords": [27.4728, 94.9120], "river": "Brahmaputra", "danger_level": 105.5},
    "Jorhat": {"coords": [26.7509, 94.2037], "river": "Brahmaputra", "danger_level": 85.3},
    "Silchar": {"coords": [24.8333, 92.7789], "river": "Barak", "danger_level": 18.5},
    "Tezpur": {"coords": [26.6528, 92.7926], "river": "Brahmaputra", "danger_level": 67.2},
    "Barpeta": {"coords": [26.3239, 91.0050], "river": "Brahmaputra", "danger_level": 46.8},
    "Dhubri": {"coords": [26.0237, 89.9840], "river": "Brahmaputra", "danger_level": 27.5},
    "Goalpara": {"coords": [26.1669, 90.6165], "river": "Brahmaputra", "danger_level": 30.2},
    "Nagaon": {"coords": [26.3477, 92.6839], "river": "Brahmaputra", "danger_level": 42.3},
    "Lakhimpur": {"coords": [27.2365, 94.1108], "river": "Brahmaputra", "danger_level": 95.8}
}

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-high {
        background: #dc2626;
        padding: 1rem;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        text-align: center;
        animation: pulse 2s infinite;
    }
    .alert-safe {
        background: #16a34a;
        padding: 1rem;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        text-align: center;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HELPER FUNCTIONS ----------------
@st.cache_resource
def load_model():
    """Load the trained flood prediction model"""
    try:
        path = os.path.join("models", "assam_floodpkl")
        with open(path, "rb") as f:
            model = pickle.load("models\assam_floodpkl")
        return model
    except Exception as e:
        st.error(f"⚠️ Model loading failed: {str(e)}")
        return None

def fetch_weather(lat, lon):
    """Fetch current weather data from OpenWeather API"""
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        rainfall = data.get("rain", {}).get("1h", 0.0)
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind_speed = data["wind"]["speed"]
        weather_desc = data["weather"][0]["description"]

        return {
            "rainfall": rainfall,
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "description": weather_desc,
            "success": True
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Weather API Error: {str(e)}")
        return {"success": False}

def calculate_risk_level(prediction, water_level, danger_level, rainfall):
    """Calculate comprehensive risk level"""
    if prediction == 0:
        return "Low"
    
    water_ratio = water_level / danger_level
    
    if water_ratio > 0.95 or rainfall > 100:
        return "Critical"
    elif water_ratio > 0.85 or rainfall > 50:
        return "High"
    elif water_ratio > 0.75 or rainfall > 25:
        return "Moderate"
    else:
        return "Low"

def create_gauge_chart(water_level, danger_level):
    """Create a gauge chart for water level"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = water_level,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Water Level (m)", 'font': {'size': 20}},
        delta = {'reference': danger_level, 'increasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [None, danger_level * 1.2], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, danger_level * 0.7], 'color': '#22c55e'},
                {'range': [danger_level * 0.7, danger_level * 0.85], 'color': '#eab308'},
                {'range': [danger_level * 0.85, danger_level], 'color': '#f97316'},
                {'range': [danger_level, danger_level * 1.2], 'color': '#dc2626'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': danger_level
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_map(districts_to_show, predictions_data):
    """Create an interactive map with flood predictions"""
    # Center map on Assam
    m = folium.Map(location=[26.2006, 92.9376], zoom_start=7)
    
    for district, pred_data in predictions_data.items():
        coords = district_data[district]["coords"]
        risk = pred_data["risk"]
        
        # Color coding
        color_map = {
            "Critical": "darkred",
            "High": "red",
            "Moderate": "orange",
            "Low": "green"
        }
        color = color_map.get(risk, "gray")
        
        # Create popup content
        popup_html = f"""
        <div style='width: 200px'>
            <h4>{district}</h4>
            <b>Risk Level:</b> {risk}<br>
            <b>River:</b> {district_data[district]['river']}<br>
            <b>Water Level:</b> {pred_data.get('water_level', 'N/A')} m<br>
            <b>Rainfall:</b> {pred_data.get('rainfall', 'N/A')} mm
        </div>
        """
        
        folium.CircleMarker(
            location=coords,
            radius=15,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{district}: {risk} Risk"
        ).add_to(m)
    
    return m

# ---------------- MAIN APP ----------------
def main():
    # Header
    st.markdown('<h1 class="main-header">🌊 Assam Flood Prediction System</h1>', unsafe_allow_html=True)
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load model
    model = load_model()
    if model is None:
        st.warning("⚠️ Running in demo mode without ML model")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        mode = st.radio(
            "Select Mode",
            ["Single District Analysis", "Multi-District Overview"],
            help="Choose between detailed single district analysis or overview of multiple districts"
        )
        
        st.divider()
        
        if mode == "Single District Analysis":
            selected_district = st.selectbox(
                "📍 Select District",
                list(district_data.keys()),
                help="Choose a district for detailed flood prediction"
            )
            
            auto_fetch = st.checkbox("Auto-fetch weather data", value=True)
            
            st.divider()
            st.subheader("Manual Input")
            
            if auto_fetch:
                water_level = st.number_input(
                    "River Water Level (m)",
                    min_value=0.0,
                    max_value=200.0,
                    value=district_data[selected_district]["danger_level"] * 0.6,
                    step=0.5,
                    help="Current water level at the monitoring station"
                )
            else:
                col1, col2 = st.columns(2)
                with col1:
                    rainfall = st.number_input("Rainfall (mm)", 0.0, 500.0, 0.0, 1.0)
                    temperature = st.number_input("Temperature (°C)", -10.0, 50.0, 25.0, 0.5)
                with col2:
                    humidity = st.number_input("Humidity (%)", 0, 100, 70, 1)
                    water_level = st.number_input("Water Level (m)", 0.0, 200.0, 30.0, 0.5)
        else:
            selected_districts = st.multiselect(
                "Select Districts",
                list(district_data.keys()),
                default=list(district_data.keys())[:5],
                help="Choose districts to monitor"
            )
            
            st.info("💡 Using simulated data for multi-district overview")
    
    # Main Content
    if mode == "Single District Analysis":
        st.header(f"📊 Flood Analysis: {selected_district}")
        
        # Display district info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("River", district_data[selected_district]["river"])
        with col2:
            st.metric("Danger Level", f"{district_data[selected_district]['danger_level']} m")
        with col3:
            st.metric("Coordinates", f"{district_data[selected_district]['coords']}")
        
        st.divider()
        
        if st.button("🚨 Run Flood Prediction", type="primary", use_container_width=True):
            with st.spinner("Analyzing flood risk..."):
                lat, lon = district_data[selected_district]["coords"]
                danger_level = district_data[selected_district]["danger_level"]
                
                # Fetch weather if auto mode
                if auto_fetch:
                    weather = fetch_weather(lat, lon)
                    if weather["success"]:
                        rainfall = weather["rainfall"]
                        temperature = weather["temperature"]
                        humidity = weather["humidity"]
                        
                        st.success("✅ Weather data fetched successfully")
                    else:
                        st.error("❌ Could not fetch weather data. Using default values.")
                        rainfall, temperature, humidity = 0.0, 25.0, 70
                
                # Prepare input
                input_data = pd.DataFrame(
                    [[rainfall, water_level, temperature, humidity]],
                    columns=["rainfall", "water_level", "temperature", "humidity"]
                )
                
                # Predict
                if model:
                    prediction = model.predict(input_data)[0]
                    try:
                        probability = model.predict_proba(input_data)[0]
                        flood_prob = probability[1] * 100
                    except:
                        flood_prob = 75 if prediction == 1 else 25
                else:
                    # Fallback prediction logic
                    prediction = 1 if (water_level > danger_level * 0.8 or rainfall > 50) else 0
                    flood_prob = 75 if prediction == 1 else 25
                
                risk_level = calculate_risk_level(prediction, water_level, danger_level, rainfall)
                
                # Display Results
                st.divider()
                
                # Alert Banner
                if prediction == 1:
                    st.markdown(f'<div class="alert-high">⚠️ FLOOD ALERT: {risk_level.upper()} RISK - {flood_prob:.1f}% Probability</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert-safe">✅ NO IMMEDIATE FLOOD THREAT DETECTED</div>', unsafe_allow_html=True)
                
                st.write("")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🌧️ Rainfall", f"{rainfall} mm")
                with col2:
                    st.metric("🌡️ Temperature", f"{temperature}°C")
                with col3:
                    st.metric("💧 Humidity", f"{humidity}%")
                with col4:
                    st.metric("📊 Flood Probability", f"{flood_prob:.1f}%")
                
                # Gauge Chart
                st.plotly_chart(create_gauge_chart(water_level, danger_level), use_container_width=True)
                
                # Recommendations
                st.subheader("📋 Recommendations")
                if risk_level == "Critical":
                    st.error("""
                    - 🚨 **IMMEDIATE EVACUATION** recommended for low-lying areas
                    - 📞 Contact local disaster management authorities
                    - 🎒 Prepare emergency kits and important documents
                    - 📻 Monitor official weather updates continuously
                    """)
                elif risk_level == "High":
                    st.warning("""
                    - ⚠️ Move to higher ground if in flood-prone areas
                    - 🎒 Keep emergency supplies ready
                    - 📱 Stay connected with local authorities
                    - 🚗 Avoid traveling unless necessary
                    """)
                elif risk_level == "Moderate":
                    st.info("""
                    - 👀 Monitor weather conditions closely
                    - 📦 Prepare emergency supplies as precaution
                    - 🔍 Stay informed about water level updates
                    """)
                else:
                    st.success("""
                    - ✅ Continue normal activities
                    - 📰 Stay updated with weather forecasts
                    - 🌊 Remain aware of seasonal flood patterns
                    """)
                
                # Map
                st.subheader("🗺️ Location Map")
                predictions_data = {
                    selected_district: {
                        "risk": risk_level,
                        "water_level": water_level,
                        "rainfall": rainfall
                    }
                }
                flood_map = create_map([selected_district], predictions_data)
                st_folium(flood_map, width=None, height=400)
    
    else:
        # Multi-District Overview
        st.header("🗺️ Multi-District Flood Monitoring")
        
        if not selected_districts:
            st.warning("Please select at least one district from the sidebar")
            return
        
        predictions_data = {}
        
        # Simulate predictions for multiple districts
        for district in selected_districts:
            # Simulate data
            danger_level = district_data[district]["danger_level"]
            water_level = np.random.uniform(danger_level * 0.5, danger_level * 1.1)
            rainfall = np.random.uniform(0, 100)
            
            # Simple prediction
            prediction = 1 if (water_level > danger_level * 0.8 or rainfall > 50) else 0
            risk_level = calculate_risk_level(prediction, water_level, danger_level, rainfall)
            
            predictions_data[district] = {
                "risk": risk_level,
                "water_level": round(water_level, 2),
                "rainfall": round(rainfall, 2),
                "danger_level": danger_level,
                "river": district_data[district]["river"]
            }
        
        # Display map
        flood_map = create_map(selected_districts, predictions_data)
        st_folium(flood_map, width=None, height=500)
        
        # Summary table
        st.subheader("📊 District Summary")
        
        df = pd.DataFrame.from_dict(predictions_data, orient='index')
        df = df.reset_index().rename(columns={'index': 'District'})
        
        # Color code risk levels
        def color_risk(val):
            colors = {
                'Critical': 'background-color: #dc2626; color: white',
                'High': 'background-color: #f97316; color: white',
                'Moderate': 'background-color: #eab308; color: black',
                'Low': 'background-color: #22c55e; color: white'
            }
            return colors.get(val, '')
        
        styled_df = df.style.applymap(color_risk, subset=['risk'])
        st.dataframe(styled_df, use_container_width=True)
    
    # Footer
    st.divider()
    st.caption("🌊 Assam Flood Prediction System | Powered by OpenWeather API & Machine Learning")
    st.caption(f"Data Source: OpenWeather | Model: Trained on historical flood data")

if __name__ == "__main__":
    main()









