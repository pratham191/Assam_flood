# import streamlit as st
# import pandas as pd
# import pickle

# # ---------------- PAGE CONFIG ----------------
# st.set_page_config(
#     page_title="Assam Flood Prediction",
#     page_icon="🌊",
#     layout="centered"
# )

# # ---------------- LOAD MODEL ----------------
# @st.cache_resource
# def load_model():
#     with open("models\assam_floodpkl", "rb") as f:
#         model = pickle.load(f)
#     return model

# model = load_model()

# # ---------------- TITLE ----------------
# st.title("🌊 Assam Flood Prediction System")
# st.markdown(
#     "Predict floods before they strike — **saving lives through intelligent forecasting**."
# )

# st.divider()

# # ---------------- USER INPUT ----------------
# st.subheader("📊 Enter Environmental Details")

# rainfall = st.number_input("Rainfall (mm)", min_value=0.0, step=1.0)
# water_level = st.number_input("River Water Level (m)", min_value=0.0, step=0.1)
# temperature = st.number_input("Temperature (°C)", min_value=0.0, step=0.1)
# humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=1.0)

# # Example categorical input
# district = st.selectbox(
#     "District",
#     ["Dibrugarh", "Guwahati", "Jorhat", "Silchar", "Tezpur"]
# )

# # ---------------- PREDICTION ----------------
# if st.button("🚨 Predict Flood"):
    
#     input_data = pd.DataFrame({
#         "rainfall": [rainfall],
#         "water_level": [water_level],
#         "temperature": [temperature],
#         "humidity": [humidity],
#         # encode district manually if used during training
#         "district": [district]
#     })

#     # If you used label encoding / one-hot encoding,
#     # apply SAME preprocessing here before prediction

#     prediction = model.predict(input_data)[0]

#     st.divider()

#     if prediction == 1:
#         st.error("⚠️ Flood Alert: HIGH RISK of Flood")
#     else:
#         st.success("✅ No Flood Expected")

# # ---------------- FOOTER ----------------
# st.markdown("---")
# st.caption("Developed for Hackathon | Assam Flood Prediction Project")




import streamlit as st
import pandas as pd
import pickle
import os

st.set_page_config(
    page_title="Assam Flood Prediction",
    page_icon="🌊",
    layout="centered"
)

@st.cache_resource
def load_model():
    model_path = os.path.join("models", "assam_floodpkl")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model

model = load_model()

st.title("🌊 Assam Flood Prediction System")
st.markdown("Predict floods before they strike — **saving lives through intelligent forecasting**.")
st.divider()

st.subheader("📊 Enter Environmental Details")

rainfall = st.number_input("Rainfall (mm)", min_value=0.0)
water_level = st.number_input("River Water Level (m)", min_value=0.0)
temperature = st.number_input("Temperature (°C)", min_value=0.0)
humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0)

if st.button("🚨 Predict Flood"):
    input_data = pd.DataFrame(
        [[rainfall, water_level, temperature, humidity]],
        columns=["rainfall", "water_level", "temperature", "humidity"]
    )

    prediction = model.predict(input_data)[0]

    st.divider()

    if prediction == 1:
        st.error("⚠️ Flood Alert: HIGH RISK of Flood")
    else:
        st.success("✅ No Flood Expected")

st.markdown("---")
st.caption("Developed for Hackathon | Assam Flood Prediction Project")
