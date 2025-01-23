import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

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
        ("System Status", "Temperature", "Soil moisture level", "Rain/Precipitation","Humidity", "Predictions" )
    )

    # Tabs for organizing content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", "Irrigation Control", "Analytics", "Settings", "About" ])

    # Tab 1: Home
    with tab1:
        st.header("Home")
        st.write("For support, contact us at deniseyoku@gmail.com.")

    # Tab 2: Irrigation Control
    with tab2:
        st.header("Irrigation Control")
        if not st.session_state["microcontroller_ip"]:
            st.error("Please set the Microcontroller IP in the Settings tab before enabling the system.")
        elif st.button("Enable system"):
            url = f"http://{st.session_state['microcontroller_ip']}/toggle_led"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    st.success("System enabled successfully!")
                else:
                    st.error(f"Failed to enable system. Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to microcontroller: {e}")

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
           

        # Change Password
       # st.subheader("Change Password")
        #new_password = st.text_input("New Password", type="password", key="new_password")
        #confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        #if st.button("Change Password"):
         #   if new_password and new_password == confirm_password:
          #      st.session_state["passwords"][st.session_state["username"]] = new_password
           #     st.success("Password updated successfully!")
            #else:
             #   st.error("Passwords do not match or are empty.")

    # Tab 5: About
    with tab5:
        st.header("About")
        st.write("This app allows you to monitor and control an IoT-based low-cost intelligent irrigation system using the MQTT protocol.")
        st.write("Designed with Streamlit, the app provides an intuitive user interface.")

