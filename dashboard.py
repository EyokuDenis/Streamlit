import streamlit as st
import requests
import json
import paho.mqtt.publish as publish
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.express as px
import paho.mqtt.client as mqtt
from paho.mqtt import client as mqtt_client
import json
from datetime import datetime
import time
import pytz
from datetime import datetime, timedelta
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_fixed
from streamlit_autorefresh import st_autorefresh
import tenacity
from requests.exceptions import ConnectionError  # Adjust based on your library
import socket

# Page configuration
st.set_page_config(page_title="Irrigation Control App", layout="wide", page_icon="💡")

# Constants
SUPABASE_URL = "https://psaukwwamurcsogzbzlc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBzYXVrd3dhbXVyY3NvZ3piemxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg0MTc1ODIsImV4cCI6MjA1Mzk5MzU4Mn0._53uMlSicurNxIEiB22n78glymGgLLVclTCDnkiGfbw"
API_KEY = "fdd252c4cd735e799c4c7bbaee0f02ee"
LAT = "1.7153"
LON = "33.6119"
MQTT_BROKER = "mqtt.eclipseprojects.io"
#BROKER = "mqtt.eclipseprojects.io"
#mqtt.eclipseprojects.io
#broker.mqtt.cool
#broker.hivemq.com
PORT = 1883
TOPIC = "pump/status"
CLIENT_ID = f"streamlit-client-{datetime.now().timestamp()}"
MQTT_TOPIC = "weather/rain"
DEFAULT_TABLE = "garden_1"
TABLES = ["garden_1", "garden_2"]
EAT_TZ = pytz.timezone('Africa/Nairobi')

# Global variable to store status
system_status = "Waiting for status..."

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(TOPIC)
        print(f"Connected and subscribed to {TOPIC}")
    else:
        print(f"Connection failed with code {rc}")
        
def on_message(client, userdata, msg):
    global system_status
    payload = msg.payload.decode()
    print(f"Received message: {payload}")  # Debug print
    
    if payload.lower() == "high":
        system_status = "🟢 Irrigation system running"
    elif payload.lower() == "low":
        system_status = "🔴 Irrigation system not running"
    else:
        system_status = f"Unknown status: {payload}"
    
# Set up MQTT client
client = mqtt_client.Client(client_id=CLIENT_ID, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker
try:
    client.connect(MQTT_BROKER, PORT) #changed
    client.loop_start()
except Exception as e:
    st.error(f"Failed to connect to MQTT broker: {e}")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize session state
def init_session_state():
    defaults = {
        "theme": "dark",
        "primary_color": "#121212",
        "text_color": "#ffffff",
        "microcontroller_ip": "",
        "is_authenticated": False,
        "username": "",
        "passwords": {"irrigate_ug": "admin123"},
        "latest_data": pd.DataFrame(),
        "selected_table": DEFAULT_TABLE
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# CSS styling
def apply_css():
    css = f"""
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
    }}
    .stRadio > label, .stTabs [role="tablist"] button {{
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
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }}
    header {{
        background-color: #1e1e1e !important;
        border-bottom: 1px solid #444444 !important;
    }}
    .stTabs [role="tablist"] button[aria-selected="true"] {{
        background-color: #444444;
        border: none;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_css()

# Login function
def login():
    st.title("Welcome to the Irrigation Control App")
    st.write("Please log in to access the application.")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    if st.button("Login"):
        if username in st.session_state["passwords"] and st.session_state["passwords"][username] == password:
            st.session_state["is_authenticated"] = True
            st.session_state["username"] = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# Data fetching function for plots (last 24 hours, EAT-adjusted)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_data(table_name):
    try:
        # Calculate time range for the last 24 hours in EAT, then convert to UTC for query
        now_eat = datetime.now(EAT_TZ)
        time_24h_ago_eat = now_eat - timedelta(hours=24)
        time_24h_ago_utc = time_24h_ago_eat.astimezone(pytz.UTC)
        time_24h_ago_str = time_24h_ago_utc.isoformat()
        
        # Debug output (fixed string)
        st.write(f"Fetching data for plots from {table_name} between {time_24h_ago_eat.strftime('%Y-%m-%d %H:%M:%S %Z')} and {now_eat.strftime('%Y-%m-%d %H:%M:%S %Z')} (EAT)")
        
        # Query data for the last 24 hours (assuming created_at is in UTC)
        response = (supabase.table(table_name)
                   .select("*")
                   .gte("created_at", time_24h_ago_str)
                   .order("created_at", desc=True)
                   .execute())
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        
        if not df.empty and 'created_at' in df.columns:
            # Convert already timezone-aware created_at to EAT
            df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert(EAT_TZ)
            latest_time = df['created_at'].max()
            st.write(f"Latest timestamp in plot data: {latest_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            st.write("No data returned for the last 24 hours.")
        
        return df
    except Exception as e:
        st.error(f"Error fetching plot data from {table_name}: {e}")
        raise

# Data fetching function for download (all data)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_all_data(table_name):
    try:
        # Query all data from the table
        response = (supabase.table(table_name)
                   .select("*")
                   .order("created_at", desc=True)
                   .execute())
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        
        if not df.empty and 'created_at' in df.columns:
            # Convert already timezone-aware created_at to EAT
            df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert(EAT_TZ)
            st.write(f"Total rows fetched for download from {table_name}: {len(df)}")
        else:
            st.write(f"No data available in {table_name} for download.")
        
        return df
    except Exception as e:
        st.error(f"Error fetching all data from {table_name}: {e}")
        raise

# Real-time subscription (for plots, using last 24 hours)
def subscribe_to_updates(table_name):
    def on_update(payload):
        st.session_state['latest_data'] = fetch_data(table_name)
        st.rerun()

    try:
        supabase.table(table_name).on('INSERT', on_update).subscribe()
        st.success(f"Subscribed to real-time updates for {table_name}")
    except Exception as e:
        st.error(f"Failed to subscribe to real-time updates: {e}")

# Plotting function with moisture selection
def plot_data(df, analytics_option, moisture_column=None):
    plots = {
        "Temperature": ("temperature", "Temperature over Time"),
        "Humidity": ("humidity", "Humidity over Time"),
        "Soil moisture level": (moisture_column, f"Soil Moisture ({moisture_column}) over Time"),
        "Rain/Precipitation": ("rain", "Rain over Time")
    }
    
    if analytics_option in plots:
        column, title = plots[analytics_option]
        if column and column in df.columns:
            fig = px.line(df, x='created_at', y=column, title=f"{title} (Last 24 Hours)")
            fig.update_layout(xaxis_title="Time (EAT)")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Last updated: {datetime.now(EAT_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            st.warning(f"'{column}' column not found in the dataset.")

# Main app
def main_app():
    # Sidebar
    with st.sidebar:
        st.header("Options")
        analytics_option = st.radio(
            "Analytics Options",
            ("Temperature", "Soil moisture level", "Rain/Precipitation", "Humidity")
        )

    # Tabs
    tabs = st.tabs(["Home", "Irrigation Control", "Analytics", "Settings", "Predictions", "System Status", "About"])

    # Home
    with tabs[0]:
        st.header("Home")
        st.write("For support, contact us at deniseyoku@gmail.com.")

    # Irrigation Control
    with tabs[1]:
        st.header("Irrigation Control")
        # Initialize message in session state if not present
        if "control_message" not in st.session_state:
            try:
                publish.single("system/enable", "auto", hostname=MQTT_BROKER)
                st.session_state["control_message"] = "System is in automatic mode"
            except Exception as e:
                st.error(f"Failed to publish to MQTT: {e}")
                st.session_state["control_message"] = "No action taken yet"

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Run"):
                try:
                    publish.single("system/enable", "high", hostname=MQTT_BROKER)
                    st.session_state["control_message"] = "System instructed to start"
                except Exception as e:
                    st.error(f"Failed to publish to MQTT: {e}")

        with col2:
            if st.button("Stop"):
                try:
                    publish.single("system/enable", "low", hostname=MQTT_BROKER)
                    st.session_state["control_message"] = "System instructed to stop"
                except Exception as e:
                    st.error(f"Failed to publish to MQTT: {e}")

        with col3:
            if st.button("Auto"):
                try:
                    publish.single("system/enable", "auto", hostname=MQTT_BROKER)
                    st.session_state["control_message"] = "System is in automatic mode"
                except Exception as e:
                    st.error(f"Failed to publish to MQTT: {e}")

            # Display the retained message
        st.success(st.session_state["control_message"])

       
    # Analytics
    with tabs[2]:
        st.header("Analytics")
        table_name = st.selectbox("Select Table", TABLES, index=TABLES.index(st.session_state["selected_table"]))
            
        moisture_column = None
        if analytics_option == "Soil moisture level":
            moisture_column = st.selectbox("Select Moisture Sensor", ["moisture_1", "moisture_2", "moisture_3"])
            
        if table_name != st.session_state["selected_table"]:
            st.session_state["selected_table"] = table_name
            st.session_state["latest_data"] = fetch_data(table_name)
            subscribe_to_updates(table_name)
            
        if "latest_data" not in st.session_state or st.session_state["latest_data"].empty:
            st.session_state["latest_data"] = fetch_data(table_name)
            subscribe_to_updates(table_name)

        df = st.session_state["latest_data"]
        if not df.empty:
            fig = plot_data(df, analytics_option, moisture_column)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"Last updated: {datetime.now(EAT_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            if st.button("Refresh Data"):
                st.session_state["latest_data"] = fetch_data(table_name)
                st.rerun()
            st_autorefresh(interval=5000, key="data_refresh")
                
            all_data_df = fetch_all_data(table_name)
            if not all_data_df.empty:
                csv = all_data_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"Download All {table_name} Data as CSV",
                    data=csv,
                    file_name=f"{table_name}_all_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No data available in {table_name} to download.")
        else:
            st.warning(f"No data found in {table_name} for the last 24 hours.")


    # Settings
    with tabs[3]:
        st.header("Settings")
        st.subheader("Theme settings")
        theme = st.radio("Select Theme", ("dark", "light"))
        try:
            if theme == "dark":
                st.session_state["theme"] = "dark"
                st.session_state["primary_color"] = "#121212"
                st.session_state["text_color"] = "#ffffff"
            else:
                st.session_state["theme"] = "light"
                st.session_state["primary_color"] = "#ffffff"
                st.session_state["text_color"] = "#000000"
        except Exception as e:
            logger.error(f"Error setting theme: {e}")
            st.error("Failed to update theme")

            @st.cache_data(ttl=3600)
            def get_settings_css(theme):
                sidebar_color = "#121212" if theme == "dark" else "#ffffff"
                header_color = "#121212" if theme == "dark" else "#ffffff"
                tab_highlight = "#444444" if theme == "dark" else "transparent"
                button_bg = "#444444" if theme == "dark" else "#007BFF"
                button_hover = "#666666" if theme == "dark" else "#007BFF"
                button_active = "#444444" if theme == "dark" else "#007BFF"
                button_border = "1px solid #666666" if theme == "dark" else "1px solid #007BFF"
                return f"""
                <style>
                    section[data-testid="stSidebar"] {{
                        background-color: {sidebar_color} !important;
                    }}
                    [data-testid="stHeader"] {{
                        background-color: {header_color} !important;
                        border-bottom: none !important;
                        box-shadow: none !important;
                    }}
                    .stApp {{
                        background-color: {st.session_state["primary_color"]} !important;
                        color: {st.session_state["text_color"]} !important;
                    }}
                    .stTabs [role="tablist"] button[aria-selected="true"] {{
                        background-color: {tab_highlight};
                        border-bottom: none;
                    }}
                    .stButton>button {{
                        background-color: {button_bg};
                        color: {st.session_state["text_color"]};
                        border-radius: 8px;
                        padding: 10px 20px;
                        border: {button_border};
                    }}
                    .stButton>button:hover {{
                        background-color: {button_hover};
                        border: {button_border};
                    }}
                    .stButton>button:active, .stButton>button:focus {{
                        background-color: {button_active};
                        border: {button_border};
                        outline: none;
                    }}
                </style>
                """

            def apply_settings_css():
                css = get_settings_css(st.session_state["theme"])
                st.markdown(css, unsafe_allow_html=True)

            apply_settings_css()

            if st.button("Apply Theme"):
                try:
                    apply_settings_css()
                    st.success("Theme updated successfully!")
                except Exception as e:
                    logger.error(f"Error applying theme: {e}")
                    st.error("Failed to apply theme")

    # Predictions
    with tabs[4]:
        st.header("Rain Prediction")
        st_autorefresh(interval=60000, key="weather_refresh")
        
        def fetch_weather_forecast():
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
            try:
                response = requests.get(url, timeout=5)
                return response.json()
            except requests.RequestException as e:
                st.error(f"Failed to fetch weather data: {e}")
                return None

        def is_rain_expected(weather_data):
            if weather_data and 'list' in weather_data:
                rain_amount = weather_data['list'][0].get('rain', {}).get('3h', 0)
                st.write(f"Rain expected in next 3 hours: {rain_amount} mm")
                return rain_amount > 0
            return False

        def publish_mqtt(rain_expected):
            try:
                publish.single(MQTT_TOPIC, json.dumps({"rain_expected": rain_expected}), hostname=MQTT_BROKER)
            except Exception as e:
                st.error(f"Failed to publish to MQTT: {e}")

        weather_data = fetch_weather_forecast()
        if weather_data:
            rain_expected = is_rain_expected(weather_data)
            publish_mqtt(rain_expected)
            st.write(f"Last checked: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # System Status
    with tabs[5]:
        st.header("System Status")
        st.write("Display system status like pump operation and data transmission.")
         # Placeholder for status display
        status_placeholder = st.empty()
    
    # Add a manual refresh button as backup
        refresh_button = st.button("Manual Refresh")
    
    # Auto-update mechanism
        status_placeholder.markdown(f"**Current Status:** {system_status}")
# Call st_autorefresh without storing the return value
        st_autorefresh(interval=3000, key="refresh_key")  # Refreshes every 3 seconds
        time.sleep(1)  # Update every second
        if refresh_button:  # If manual refresh is clicked
            st.rerun()  # Using rerun for Streamlit 2.1
        
    # About
    with tabs[6]:
        st.header("About")
        st.write("This app helps automate irrigation based on weather conditions and soil moisture.")
    # Cleanup on app close
    def cleanup():
        client.loop_stop()
        client.disconnect()
if __name__ == "__main__":
    if not st.session_state["is_authenticated"]:
        login()
    else:
        main_app()