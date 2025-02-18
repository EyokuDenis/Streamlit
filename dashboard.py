import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import pickle
import os


# Set up the page configuration
st.set_page_config(page_title="Irrigation Control App", layout="wide", page_icon="💡")
df = pd.DataFrame(np.random.randn(100, 4), columns=["moisture", "rain", "temp", "humid"])

# Initialize session state for theme, colors, and user authentication
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "primary_color" not in st.session_state:
    st.session_state["primary_color"] = "#121212"
if "text_color" not in st.session_state:
    st.session_state["text_color"] = "#ffffff"
if "microcontroller_ip" not in st.session_state:
    st.session_state["microcontroller_ip"] = ""
if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "passwords" not in st.session_state:
    # Mock user data (username: password)
    st.session_state["passwords"] = {"irrigate_ug": "admin123"}

# Apply dynamic CSS for theme customization
def apply_css():
    st.markdown(
        f"""
        <style>
        body {{
            background-color: {st.session_state["primary_color"]};
            color: {st.session_state["text_color"]};
            font-family: 'Arial', sans-serif;
        }}
        .stApp {{
            background-color: {st.session_state["primary_color"]};
            color: {st.session_state["text_color"]} !important;
        }}
        .stSidebar {{
            background-color: #1e1e1e;
            color: {st.session_state["text_color"]} !important;
        }}
        .stRadio > label {{
            color: {st.session_state["text_color"]} !important;
        }}
        .stButton>button {{
            background-color: #444444;
            color: {st.session_state["text_color"]};
            border-radius: 8px;
            padding: 10px 20px;
            border: 1px solid #666666;
        }}
        .stButton>button:hover {{
            background-color: #666666;
            border: 1px solid #888888;
        }}
        div[data-testid="stVerticalBlock"] {{
            background-color: {st.session_state["primary_color"]};
            color: {st.session_state["text_color"]} !important;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }}
        header {{
            background-color: #1e1e1e !important;
            color: {st.session_state["text_color"]} !important;
            border-bottom: 1px solid #444444 !important;
        }}
        .stTabs [role="tablist"] button {{
            color: {st.session_state["text_color"]} !important;
        }}
        .stTabs [role="tablist"] button[aria-selected="true"] {{
            background-color: #444444;
            color: {st.session_state["text_color"]} !important;
            border: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_css()

# Login Functionality
def login():
    username = st.text_input("Username", key="login_username", placeholder="Enter your username")
    password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
    if st.button("Login"):
        if username in st.session_state["passwords"] and st.session_state["passwords"][username] == password:
            st.session_state["is_authenticated"] = True
            st.session_state["username"] = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password.")

# Main App Content (only accessible after login)
if not st.session_state["is_authenticated"]:
    st.title("Welcome to the Irrigation Control App")
    st.write("Please log in to access the application.")
    login()
else:
    # Sidebar with radio buttons
    st.sidebar.header("Options")
    analytics_option = st.sidebar.radio(
        "Analytics Options",
        ("Temperature", "Soil moisture level", "Rain/Precipitation", "Humidity")
    )

    # Tabs for organizing content
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Home", "Irrigation Control", "Analytics", "Settings", "Predictions", "System status", "About"])

    # Tab 1: Home
    with tab1:
        st.header("Home")
        st.write("For support, contact us at deniseyoku@gmail.com.")

    # Tab 2: Irrigation Control
    with tab2:
        st.header("Irrigation Control")
        if not st.session_state["microcontroller_ip"]:
            st.error("Please set the Microcontroller IP in the Settings tab before enabling the system.")
        else:
            if st.button("Enable system"):
                url = f"http://{st.session_state['microcontroller_ip']}/toggle_led"
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        st.success("System enabled successfully!")
                    else:
                        st.error(f"Failed to enable system. Status code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to microcontroller: {e}")
            # Visual system status indicator
            if st.session_state.get("is_authenticated"):
                st.write("Irrigation System Status: Enabled")

    # Tab 3: Analytics
    with tab3:
        st.header("Analytics")
        if analytics_option == "System Status":
            st.write("Displaying system running status...")
            st.line_chart(df)
        elif analytics_option == "Temperature":
            st.write("Displaying temperature logs...")
            st.line_chart(df[["temp"]])
        elif analytics_option == "Humidity":
            st.write("Displaying humidity logs...")
            st.line_chart(df[["humid"]])
        elif analytics_option == "Soil moisture level":
            st.write("Displaying soil moisture level logs...")
            st.line_chart(df[["moisture"]])
        elif analytics_option == "Rain/Precipitation":
            st.write("Displaying rain/precipitation logs...")
            st.line_chart(df[["rain"]])
        elif analytics_option == "Predictions":
            st.write("Displaying possibility of rainfall...")

    # Tab 4: Settings
    with tab4:
        st.header("Settings")
        st.write("Configure your application settings below.")

        # Microcontroller IP
        microcontroller_ip = st.text_input(
            "Microcontroller IP Address",
            value=st.session_state["microcontroller_ip"],
            placeholder="Enter the IP Address",
        )
        if microcontroller_ip:
            st.session_state["microcontroller_ip"] = microcontroller_ip

        # Theme Selector
        theme = st.radio("Select Theme", ("dark", "light"))
        if theme == "dark":
            st.session_state["theme"] = "dark"
            st.session_state["primary_color"] = "#121212"
            st.session_state["text_color"] = "#ffffff"
        else:
            st.session_state["theme"] = "light"
            st.session_state["primary_color"] = "#f0f0f0"
            st.session_state["text_color"] = "#000000"

        # Custom Colors
        primary_color = st.color_picker("Primary Background Color", st.session_state["primary_color"])
        text_color = st.color_picker("Text Color", st.session_state["text_color"])
        st.session_state["primary_color"] = primary_color
        st.session_state["text_color"] = text_color

        # Apply changes
        if st.button("Apply Theme"):
            apply_css()
            st.success("Theme updated successfully!")

    # Tab 5: Predictions
    with tab5:
        st.header("Rain Prediction")

        # Define the model path
        model_path = 'rainfall_model_tuned.pkl'
        
        # Check if the model file exists
        if os.path.exists(model_path) and os.path.isfile(model_path):
            try:
                with open(model_path, 'rb') as model_file:
                    prediction_model = pickle.load(model_file)
            except Exception as e:
                st.error(f"Error loading the model: {e}")
        else:
            st.error(f"Model file not found. Please check the file path. Current path: {os.getcwd()}")

        def rain_prediction(input_data):
            input_array = np.array(input_data).reshape(1, -1)
            try:
                prediction = prediction_model.predict(input_array)[0]
                if prediction < 0.1:
                    return "No rain"
                elif prediction < 2:
                    return "Light rain"
                elif prediction < 5:
                    return "Moderate rain"
                elif prediction < 10:
                    return "Rain"
                elif prediction < 20:
                    return "Strong rain"
                elif prediction < 50:
                    return "Heavy rain"
                elif prediction < 100:
                    return "Very heavy rain"
                else:
                    return "Extremely heavy rain"
            except Exception as e:
                st.error(f"Prediction error: {e}")
                return "Prediction failed"

        # Collect user inputs for rain prediction
        year = st.text_input('Enter year')
        day_of_year = st.text_input('Enter day of year')
        relative_humidity = st.text_input('Enter relative humidity value')
        surface_soil_wetness = st.text_input('Enter surface soil wetness value')
        profile_soil_moisture = st.text_input('Enter profile soil moisture value')
        max_temperature = st.text_input('Enter maximum temperature')
        min_temperature = st.text_input('Enter minimum temperature')

        if st.button('Predict rain'):
            if all([year, day_of_year, relative_humidity, surface_soil_wetness, profile_soil_moisture, max_temperature, min_temperature]):
                try:
                    input_data = [
                        float(year), float(day_of_year), float(relative_humidity),
                        float(surface_soil_wetness), float(profile_soil_moisture),
                        float(max_temperature), float(min_temperature)
                    ]
                    rain_likelihood = rain_prediction(input_data)
                    st.success(f"Predicted Rainfall Category: {rain_likelihood}")
                except ValueError:
                    st.error("Please enter valid numeric inputs.")
            else:
                st.warning("All input fields are required.")

    # Tab 6: System Status
    with tab6:
        st.header("System Status")
        st.write("Checking system status...")

    # Tab 7: About
    with tab7:
        st.header("About")
        st.write("This app allows you to monitor and control an IoT-based low-cost intelligent irrigation system using the MQTT protocol.")
        st.write("Designed with Streamlit, the app provides an intuitive user interface.")
