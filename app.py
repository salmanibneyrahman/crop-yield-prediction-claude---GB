import streamlit as st
import pandas as pd
import numpy as np
import joblib
import requests
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

st.set_page_config(
    page_title="Crop Yield Prediction System",
    page_icon="wheat",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
    <style>
    :root {
        --primary: #00d4ff;
        --secondary: #00ff88;
        --dark-bg: #0a0e27;
        --card-bg: #1a1f3a;
        --accent: #6366f1;
    }
    * { margin: 0; padding: 0; }
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f2847 100%);
        background-attachment: fixed;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    [data-testid="stHeader"] {
        background: transparent;
        border-bottom: 1px solid rgba(0, 212, 255, 0.1);
    }
    h1 {
        background: linear-gradient(135deg, #00d4ff 0%, #00ff88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        font-size: 3.5em !important;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        margin-bottom: 0.5em !important;
        letter-spacing: 2px;
    }
    h2 {
        color: #00d4ff;
        border-bottom: 2px solid rgba(0, 212, 255, 0.3);
        padding-bottom: 10px;
        font-weight: 700; font-size: 1.8em; letter-spacing: 1px;
    }
    [data-testid="stColumn"] {
        background: rgba(26, 31, 58, 0.5);
        border-radius: 15px;
        border: 1px solid rgba(0, 212, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        transition: all 0.3s ease;
    }
    [data-testid="stColumn"]:hover {
        border-color: rgba(0, 212, 255, 0.3);
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
        transform: translateY(-5px);
    }
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] select {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        color: #00d4ff !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-weight: 600;
    }
    body, p, span, div { color: #e0e0ff; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 12px; padding: 20px;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricLabel"] { color: #00d4ff !important; font-weight: 700; }
    [data-testid="stMetricValue"] { color: #00ff88 !important; font-size: 2.5em !important; }
    hr {
        border: none; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
        margin: 30px 0;
    }
    .section-header {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.05));
        border-left: 4px solid #00d4ff;
        padding: 15px; border-radius: 8px; margin: 20px 0;
        font-weight: 700; letter-spacing: 1px;
    }
    .result-box {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.05));
        border: 2px solid #00d4ff; border-radius: 12px;
        padding: 20px; margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
    }
    .big-result {
        font-size: 2.2em; font-weight: 900; letter-spacing: 2px; margin: 10px 0;
    }
    .image-container {
        border-radius: 15px; overflow: hidden;
        border: 2px solid rgba(0, 212, 255, 0.3); margin: 15px 0;
    }
    .about-item {
        flex: 1; min-width: 250px;
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 12px; padding: 20px; text-align: center;
    }
    .about-item h4 { color: #00d4ff; margin-bottom: 10px; font-size: 1.1em; }
    .about-item p { color: #e0e0ff; font-size: 0.95em; line-height: 1.6; margin: 5px 0; }
    .top-crop-bar {
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 8px; padding: 10px 15px; margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DISTRICT COORDINATES & ALIASES
# ============================================================================
DISTRICT_COORDS = {
    'Chattogram': (22.3569, 91.7832), 'Dhaka': (23.8103, 90.4125),
    'Barishal': (22.7010, 90.3535), 'Cumilla': (23.4607, 91.1809),
    'Bogura': (24.8466, 89.3773), 'Jashore': (23.1665, 89.2072),
    'Rajshahi': (24.3745, 88.6042), 'Khulna': (22.8456, 89.5403),
    'Sylhet': (24.8949, 91.8687), 'Rangpur': (25.7439, 89.2752),
    'Mymensingh': (24.7471, 90.4203), 'Narayanganj': (23.6238, 90.5000),
    'Gazipur': (23.9999, 90.4203), 'Narsingdi': (23.9322, 90.7151),
    'Tangail': (24.2513, 89.9164), 'Kishoreganj': (24.4449, 90.7766),
    'Manikganj': (23.8617, 90.0003), 'Munshiganj': (23.5422, 90.5305),
    'Faridpur': (23.6070, 89.8429), 'Madaripur': (23.1641, 90.1978),
    'Gopalganj': (23.0488, 89.8266), 'Shariatpur': (23.2423, 90.4348),
    'Bagerhat': (22.6512, 89.7857), 'Satkhira': (22.7185, 89.0726),
    'Narail': (23.1725, 89.5127), 'Magura': (23.4873, 89.4197),
    'Jhenaidah': (23.5448, 89.1726), 'Chuadanga': (23.6402, 88.8418),
    'Kushtia': (23.9013, 89.1206), 'Meherpur': (23.7627, 88.6318),
    'Natore': (24.4206, 89.0006), 'Pabna': (24.0064, 89.2372),
    'Sirajganj': (24.4534, 89.7000), 'Chapai Nawabganj': (24.5965, 88.2775),
    'Naogaon': (24.7936, 88.9318), 'Joypurhat': (25.0968, 89.0227),
    'Gaibandha': (25.3288, 89.5286), 'Kurigram': (25.8054, 89.6362),
    'Lalmonirhat': (25.9923, 89.2847), 'Nilphamari': (25.9315, 88.8560),
    'Dinajpur': (25.6217, 88.6354), 'Thakurgaon': (26.0336, 88.4616),
    'Panchagarh': (26.3411, 88.5542), 'Habiganj': (24.3840, 91.4147),
    'Moulvibazar': (24.4829, 91.7774), 'Sunamganj': (25.0658, 91.3950),
    'Brahmanbaria': (23.9571, 91.1112), 'Chandpur': (23.2333, 90.6712),
    'Lakshmipur': (22.9425, 90.8281), 'Noakhali': (22.8696, 91.0995),
    'Feni': (23.0101, 91.3976), 'Khagrachari': (23.1194, 91.9847),
    'Rangamati': (22.7324, 92.2985), 'Bandarban': (22.1953, 92.2184),
    "Cox'S Bazar": (21.4272, 92.0058), 'Pirojpur': (22.5791, 89.9759),
    'Jhallokati': (22.6406, 90.1987), 'Barguna': (22.1510, 90.1266),
    'Patuakhali': (22.3596, 90.3290), 'Bhola': (22.6859, 90.6482),
    'Netrokona': (24.8700, 90.7279), 'Sherpur': (25.0204, 90.0170),
    'Jamalpur': (24.9375, 89.9372), 'Rajbari': (23.7531, 89.6447),
}

# ============================================================================
# LOAD MODELS
# ============================================================================
@st.cache_resource
def load_all():
    try:
        return {
            'yield_model': joblib.load('yield_model.pkl'),
            'crop_model': joblib.load('crop_model.pkl'),
            'lr_display': joblib.load('lr_display_model.pkl'),
            'le_crop': joblib.load('le_crop.pkl'),
            'le_reencode': joblib.load('le_reencode.pkl'),
            'season_le': joblib.load('season_le.pkl'),
            'soil_le': joblib.load('soil_le.pkl'),
            'le_season': joblib.load('le_season.pkl'),
            'le_district': joblib.load('le_district.pkl'),
            'crop_scaler': joblib.load('crop_scaler.pkl'),
            'feature_columns': joblib.load('feature_columns.pkl'),
            'crop_feature_columns': joblib.load('crop_feature_columns.pkl'),
            'district_soil_map': joblib.load('district_soil_map.pkl'),
            'available_districts': joblib.load('available_districts.pkl'),
            'crop_timing': joblib.load('crop_timing.pkl'),
        }
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None

# ============================================================================
# WEATHER FUNCTION
# ============================================================================
@st.cache_data(ttl=600)
def get_weather_for_district(district_name):
    if district_name not in DISTRICT_COORDS:
        return None
    lat, lon = DISTRICT_COORDS[district_name]
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&daily=temperature_2m_max,temperature_2m_min,relative_humidity_2m_max,relative_humidity_2m_min"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})
            daily = data.get('daily', {})
            weather = {
                'avg_temp': current.get('temperature_2m'),
                'min_temp': daily.get('temperature_2m_min', [None])[0],
                'max_temp': daily.get('temperature_2m_max', [None])[0],
                'avg_humidity': current.get('relative_humidity_2m'),
                'min_humidity': daily.get('relative_humidity_2m_min', [None])[0],
                'max_humidity': daily.get('relative_humidity_2m_max', [None])[0],
                'rainfall': None
            }
            try:
                end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                rain_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=precipitation_sum"
                rain_resp = requests.get(rain_url, timeout=10)
                if rain_resp.status_code == 200:
                    precip = rain_resp.json().get('daily', {}).get('precipitation_sum', [])
                    valid = [p for p in precip if p is not None]
                    if valid:
                        weather['rainfall'] = round(sum(valid), 1)
            except:
                pass
            return weather
    except:
        pass
    return None

def find_nearest_district(lat, lon, districts_list):
    """Find the nearest district from coordinates"""
    min_dist = float('inf')
    nearest = districts_list[0]
    for d_name, (d_lat, d_lon) in DISTRICT_COORDS.items():
        if d_name in districts_list:
            dist = ((lat - d_lat)**2 + (lon - d_lon)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest = d_name
    return nearest

def apply_district_data(district_name):
    """Set soil and weather for a given district"""
    st.session_state.soil = models['district_soil_map'].get(district_name, available_soils[0])
    w = get_weather_for_district(district_name)
    if w and w.get('avg_temp') is not None:
        st.session_state.t_min = float(w['min_temp'] or 18.0)
        st.session_state.t_avg = float(w['avg_temp'] or 25.0)
        st.session_state.t_max = float(w['max_temp'] or 32.0)
        st.session_state.h_min = int(w['min_humidity'] or 40)
        st.session_state.h_avg = int(w['avg_humidity'] or 70)
        st.session_state.h_max = int(w['max_humidity'] or 95)
        if w.get('rainfall') is not None:
            st.session_state.rainfall = float(w['rainfall'])

def get_current_season():
    """Determine Bangladesh agricultural season from current date"""
    today = datetime.now()
    month = today.month
    day = today.day
    
    # Kharif-1: March 16 - June 30
    if (month == 3 and day >= 16) or (month in [4, 5]) or (month == 6):
        return 'Kharif 1'
    # Kharif-2: July 1 - October 15
    elif (month in [7, 8, 9]) or (month == 10 and day <= 15):
        return 'Kharif 2'
    # Rabi: October 16 - March 15
    else:
        return 'Rabi'

def get_season_remaining_days():
    """Calculate days remaining in current season"""
    today = datetime.now()
    month = today.month
    day = today.day
    
    # Season end dates
    # Kharif-1: ends June 30
    # Kharif-2: ends October 15
    # Rabi: ends March 15
    
    if (month == 3 and day >= 16) or month in [4, 5] or month == 6:
        # Kharif-1: ends June 30
        end = datetime(today.year, 6, 30)
        season = 'Kharif 1'
    elif month in [7, 8, 9] or (month == 10 and day <= 15):
        # Kharif-2: ends October 15
        end = datetime(today.year, 10, 15)
        season = 'Kharif 2'
    else:
        # Rabi: ends March 15
        if month >= 10:
            end = datetime(today.year + 1, 3, 15)
        else:
            end = datetime(today.year, 3, 15)
        season = 'Rabi'
    
    remaining = (end - today).days
    return season, remaining

def get_planting_warning(crop_name, season, remaining_days):
    """Check if there's enough time to plant this crop"""
    if remaining_days <= 7:
        return "critical", f"CRITICAL: Only {remaining_days} days left in {season}. This crop may not survive the season change. Consider a crop from the next season."
    elif remaining_days <= 21:
        return "warning", f"WARNING: Only {remaining_days} days left in {season}. Late planting — yields may be lower than predicted."
    elif remaining_days <= 45:
        return "caution", f"Note: {remaining_days} days left in {season}. Planting is still viable but monitor closely."
    else:
        return "safe", f"{remaining_days} days remaining in {season}. Good time to plant."

# ============================================================================
# HEADER
# ============================================================================
st.title("CROP YIELD PREDICTION SYSTEM")

st.markdown("""
<div class="image-container">
    <img src="https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=1200&q=80" style="width:100%; height:400px; object-fit:cover; border-radius:15px;" alt="Agriculture">
</div>
""", unsafe_allow_html=True)

st.markdown("---")

with st.expander("About System"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="about-item"><h4>Yield Model</h4><p><strong>Type:</strong> Decision Tree</p><p><strong>R Score:</strong> 0.8621</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="about-item"><h4>Crop Model</h4><p><strong>Type:</strong> KNN Classifier</p><p><strong>Accuracy:</strong> 0.8827</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="about-item"><h4>Training Data</h4><p><strong>Records:</strong> 169,069</p><p><strong>Location:</strong> Bangladesh</p></div>', unsafe_allow_html=True)

st.markdown("---")

models = load_all()
if models is None:
    st.error("Could not load models. Ensure all 14 .pkl files are in the app folder.")
    st.stop()

available_districts = models['available_districts']
available_seasons = list(models['season_le'].classes_)
available_soils = list(models['soil_le'].classes_)

# ============================================================================
# MODE SELECTION
# ============================================================================
st.markdown('<div class="section-header">How do you want to enter data?</div>', unsafe_allow_html=True)

def on_mode_change():
    if st.session_state.entry_mode == "Auto-Detect from Location":
        st.session_state.location_detected = False
    # Manual mode: keep current values

data_mode = st.radio(
    "Select:", ["Auto-Detect from Location", "Manual Entry"],
    horizontal=True, key="entry_mode", on_change=on_mode_change
)

is_auto = (data_mode == "Auto-Detect from Location")

st.markdown("---")

# ============================================================================
# ONE-TIME INITIALIZATION (defaults only)
# ============================================================================
if 'app_ready' not in st.session_state:
    st.session_state.district = available_districts[0]
    st.session_state.soil = models['district_soil_map'].get(available_districts[0], available_soils[0])
    st.session_state.t_min = 18.0
    st.session_state.t_avg = 25.0
    st.session_state.t_max = 32.0
    st.session_state.h_min = 40
    st.session_state.h_avg = 70
    st.session_state.h_max = 95
    st.session_state.rainfall = 150.0
    st.session_state.detected_city = None
    st.session_state.app_ready = True
    st.session_state.location_detected = False
    st.rerun()

# ============================================================================
# AUTO MODE: Browser GPS Detection
# ============================================================================
if is_auto and not st.session_state.get('location_detected', False):
    st.markdown("""
    <div style="background: rgba(0,212,255,0.1); border: 1px solid rgba(0,212,255,0.3); 
         border-radius: 10px; padding: 15px; margin: 10px 0;">
        <p style="color: #00d4ff; font-weight: 700; font-size: 1.1em;">
            Detecting your location via browser GPS...</p>
        <p style="color: #aab;">Please click "Allow" when your browser asks for location permission.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get browser GPS location
    loc = get_geolocation()
    
    if loc is not None and loc != 0 and isinstance(loc, dict) and 'coords' in loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        
        # Find nearest district
        nearest = find_nearest_district(lat, lon, available_districts)
        
        # Set district, soil, weather
        st.session_state.district = nearest
        st.session_state.detected_city = nearest
        st.session_state.location_detected = True
        apply_district_data(nearest)
        
        st.rerun()
    else:
        # Still waiting or denied
        if st.button("Skip detection - select district manually"):
            st.session_state.location_detected = True
            st.rerun()
        st.stop()

elif is_auto and st.session_state.get('location_detected', False):
    detected = st.session_state.get('detected_city')
    if detected:
        st.success(f"Location detected: {detected} | Weather, soil, and rainfall auto-loaded")
    else:
        st.info("Location skipped. Select your district below.")

# ============================================================================
# CALLBACKS
# ============================================================================
def on_district_change():
    if st.session_state.entry_mode == "Auto-Detect from Location":
        d = st.session_state.district
        apply_district_data(d)

# ============================================================================
# DATA ENTRY
# ============================================================================
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="section-header">Location and Farm Details</div>', unsafe_allow_html=True)

    selected_district = st.selectbox(
        "District", available_districts,
        key="district",
        on_change=on_district_change
    )

    if is_auto:
        selected_soil = st.selectbox(
            "Soil Type (auto-detected from district)", available_soils,
            key="soil"
        )
    else:
        selected_soil = st.selectbox(
            "Soil Type", available_soils,
            key="soil"
        )

    area_hectares = st.number_input(
        "Cultivated Area (hectares)",
        value=1000.0, min_value=0.5, max_value=10000000.0, step=100.0
    )

    if is_auto:
        # Auto-detect season from current date
        auto_season = get_current_season()
        season_idx = available_seasons.index(auto_season) if auto_season in available_seasons else 0
        selected_season = st.selectbox(
            f"Season (auto-detected: {auto_season})", 
            available_seasons, index=season_idx, key="season"
        )
    else:
        selected_season = st.selectbox("Season", available_seasons, key="season")

    rainfall = st.number_input(
        "Monthly Avg Rainfall (mm)",
        min_value=0.0, max_value=1000.0, step=10.0,
        key="rainfall"
    )

with col_right:
    st.markdown('<div class="section-header">Weather Conditions</div>', unsafe_allow_html=True)

    if is_auto:
        w_check = get_weather_for_district(selected_district)
        if w_check and w_check.get('avg_temp') is not None:
            st.success(f"Weather auto-fetched for {selected_district}")
            if w_check.get('rainfall') is not None:
                st.info(f"Rainfall (last 30 days): {w_check['rainfall']} mm")
        else:
            st.warning(f"Could not fetch weather for {selected_district}. Enter manually.")
    else:
        st.info("Manual mode: Enter all weather data manually.")

    st.subheader("Temperature (Celsius)")
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        min_temp = st.number_input("Min Temp", key="t_min")
    with tc2:
        auto_avg_temp = round((st.session_state.t_min + st.session_state.t_max) / 2, 1)
        if not is_auto:
            st.session_state.t_avg = auto_avg_temp
        avg_temp = st.number_input("Avg Temp (auto-calculated)", key="t_avg")
    with tc3:
        max_temp = st.number_input("Max Temp", key="t_max")

    st.subheader("Humidity (Percent)")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        min_humidity = st.number_input("Min Humidity", min_value=0, max_value=100, key="h_min")
    with hc2:
        auto_avg_hum = int(round((st.session_state.h_min + st.session_state.h_max) / 2))
        if not is_auto:
            st.session_state.h_avg = auto_avg_hum
        avg_humidity = st.number_input("Avg Humidity (auto-calculated)", min_value=0, max_value=100, key="h_avg")
    with hc3:
        max_humidity = st.number_input("Max Humidity", min_value=0, max_value=100, key="h_max")

st.markdown("---")

# ============================================================================
# VALIDATION
# ============================================================================
temp_valid = min_temp <= avg_temp <= max_temp
hum_valid = 0 <= min_humidity <= max_humidity <= 100

if not temp_valid:
    st.error("Temperature must be: Min <= Avg <= Max")
if not hum_valid:
    st.error("Humidity must be: 0 <= Min <= Max <= 100")

# ============================================================================
# PREDICT
# ============================================================================
st.markdown('<div class="section-header">Get Predictions</div>', unsafe_allow_html=True)

if st.button("Predict Crop and Yield", use_container_width=True, disabled=not (temp_valid and hum_valid)):
    try:
        season_encoded = int(models['season_le'].transform([selected_season])[0])
        soil_encoded = int(models['soil_le'].transform([selected_soil])[0])

        yield_df = pd.DataFrame({
            'Avg Temp': [avg_temp], 'Avg Humidity': [float(avg_humidity)],
            'Max Temp': [max_temp], 'Min Temp': [min_temp],
            'Max Relative Humidity': [float(max_humidity)],
            'Min Relative Humidity': [float(min_humidity)],
            'Monthly_Avg_Rainfall_mm': [rainfall],
            'Season_Encoded': [season_encoded], 'Soil_Encoded': [soil_encoded]
        })
        yield_df = yield_df[models['feature_columns']]
        predicted_yield = float(models['yield_model'].predict(yield_df)[0])
        total_production = predicted_yield * area_hectares

        crop_input = pd.DataFrame(0.0, index=[0], columns=models['crop_feature_columns'])
        crop_input['Avg Temp'] = avg_temp
        crop_input['Avg Humidity'] = float(avg_humidity)
        crop_input['Max Temp'] = max_temp
        crop_input['Min Temp'] = min_temp
        crop_input['Max Relative Humidity'] = float(max_humidity)
        crop_input['Min Relative Humidity'] = float(min_humidity)

        season_col = f"Season_{selected_season}"
        if season_col in crop_input.columns:
            crop_input[season_col] = 1
        district_col = f"District_{selected_district}"
        if district_col in crop_input.columns:
            crop_input[district_col] = 1
        soil_col = f"Soil_{selected_soil}"
        if soil_col in crop_input.columns:
            crop_input[soil_col] = 1

        crop_features_scaled = models['crop_scaler'].transform(crop_input)

        crop_pred_code = int(models['crop_model'].predict(crop_features_scaled)[0])
        original_code = int(models['le_reencode'].inverse_transform([crop_pred_code])[0])
        crop_name = str(models['le_crop'].inverse_transform([original_code])[0])

        lr_probas = models['lr_display'].predict_proba(crop_features_scaled)[0]
        all_indices = np.argsort(lr_probas)[::-1]  # all crops sorted by probability
        top_5_crops = []
        for idx in all_indices:
            if len(top_5_crops) >= 5:
                break
            orig = int(models['le_reencode'].inverse_transform([int(idx)])[0])
            name = str(models['le_crop'].inverse_transform([orig])[0])
            # Skip if same as KNN's primary recommendation
            if name.lower() == crop_name.lower():
                continue
            conf = float(lr_probas[idx]) * 100
            top_5_crops.append((name, conf))

        st.markdown("---")

        st.markdown(f"""
        <div class="result-box">
            <h3 style="color: #00ff88; margin-bottom: 20px; font-size: 1.8em;">Prediction Results</h3>
            <div style="display: flex; gap: 40px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 250px;">
                    <h3 style="color: #aab; font-size: 1.5em; font-weight: 700; margin-bottom: 5px;">Recommended Crop</h3>
                    <div class="big-result" style="color: #00ff88;">{crop_name.upper()}</div>
                </div>
                <div style="flex: 1; min-width: 250px;">
                    <h3 style="color: #aab; font-size: 1.5em; font-weight: 700; margin-bottom: 5px;">Predicted Yield</h3>
                    <div class="big-result" style="color: #00d4ff;">{predicted_yield:.2f}</div>
                    <div style="color: #aab; font-size: 1.1em;">tons / hectare</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # PLANTING TIMING WARNING
        current_season, current_days_left = get_season_remaining_days()
        
        # If user selected a different season than current, warn them
        if selected_season != current_season:
            warning_level = "info"
            warning_msg = f"You selected {selected_season}, but the current season is {current_season} ({current_days_left} days remaining). Predictions are based on {selected_season} conditions."
        else:
            warning_level, warning_msg = get_planting_warning(crop_name, current_season, current_days_left)
        
        # Show crop timing info if available
        timing_key = (crop_name, selected_season)
        timing_info = models['crop_timing'].get(timing_key, None)
        
        if warning_level == "info":
            st.markdown(f"""
            <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.4); 
                 border-radius: 12px; padding: 15px; margin: 15px 0;">
                <p style="color: #8b8eff; font-weight: 600;">{warning_msg}</p>
            </div>
            """, unsafe_allow_html=True)
        elif warning_level == "critical":
            st.markdown(f"""
            <div style="background: rgba(255,50,50,0.15); border: 2px solid #ff3232; 
                 border-radius: 12px; padding: 20px; margin: 15px 0;">
                <h3 style="color: #ff3232; font-size: 1.3em;">Season Timing Alert</h3>
                <p style="color: #ff6464; font-size: 1.1em; font-weight: 700;">{warning_msg}</p>
            </div>
            """, unsafe_allow_html=True)
        elif warning_level == "warning":
            st.markdown(f"""
            <div style="background: rgba(255,165,0,0.15); border: 2px solid #ffa500; 
                 border-radius: 12px; padding: 20px; margin: 15px 0;">
                <h3 style="color: #ffa500; font-size: 1.3em;">Season Timing Alert</h3>
                <p style="color: #ffb84d; font-size: 1.1em; font-weight: 700;">{warning_msg}</p>
            </div>
            """, unsafe_allow_html=True)
        elif warning_level == "caution":
            st.markdown(f"""
            <div style="background: rgba(255,255,0,0.1); border: 1px solid rgba(255,255,0,0.3); 
                 border-radius: 12px; padding: 15px; margin: 15px 0;">
                <p style="color: #ffff66; font-weight: 600;">{warning_msg}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.3); 
                 border-radius: 12px; padding: 15px; margin: 15px 0;">
                <p style="color: #00ff88; font-weight: 600;">{warning_msg}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show crop lifecycle timing
        if timing_info:
            st.markdown(f"""
            <div style="background: rgba(0,212,255,0.05); border: 1px solid rgba(0,212,255,0.2); 
                 border-radius: 10px; padding: 15px; margin: 10px 0;">
                <p style="color: #00d4ff; font-weight: 700; margin-bottom: 8px;">
                    {crop_name} Growing Calendar ({selected_season})</p>
                <p style="color: #aab;">Transplant: <span style="color: #00ff88;">{timing_info['transplant']}</span> | 
                   Growth: <span style="color: #00ff88;">{'Direct growth (no separate phase)' if 'no need' in str(timing_info['growth']).lower() or 'nan' in str(timing_info['growth']).lower() else timing_info['growth']}</span> | 
                   Harvest: <span style="color: #00ff88;">{timing_info['harvest']}</span></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="result-box"><h3 style="color: #00d4ff; font-size: 1.5em;">Top 5 Alternative Crops</h3>', unsafe_allow_html=True)
        for rank, (c_name, c_conf) in enumerate(top_5_crops, 1):
            bar_pct = min(c_conf, 100)
            bar_color = "#00ff88" if rank == 1 else "#00d4ff"
            st.markdown(f"""
            <div class="top-crop-bar">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; color:{bar_color};">{rank}. {c_name}</span>
                    <span style="color:#00d4ff; font-weight:600;">{c_conf:.1f}%</span>
                </div>
                <div style="background:rgba(255,255,255,0.1); border-radius:4px; height:8px; margin-top:5px;">
                    <div style="background:{bar_color}; width:{bar_pct}%; height:100%; border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('<p style="color:#888; font-size:0.85em; margin-top:10px;">Primary prediction: KNN | Alternative ranking: Gradient Boosting</p></div>', unsafe_allow_html=True)

        st.markdown('<div class="result-box"><h3 style="color: #00d4ff; font-size: 1.5em;">Production Forecast</h3>', unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            st.metric("Total Production", f"{total_production:,.0f}", "tons")
        with pc2:
            st.metric("Area", f"{area_hectares:,.0f}", "hectares")
        with pc3:
            st.metric("Season", selected_season)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Farm Summary")
        summary = pd.DataFrame({
            'Parameter': ['District', 'Soil Type', 'Season', 'Area (hectares)',
                         'Min Temp (C)', 'Avg Temp (C)', 'Max Temp (C)',
                         'Min Humidity (%)', 'Avg Humidity (%)', 'Max Humidity (%)',
                         'Rainfall (mm/month)'],
            'Value': [selected_district, selected_soil, selected_season, f"{area_hectares:,.0f}",
                     f"{min_temp:.1f}", f"{avg_temp:.1f}", f"{max_temp:.1f}",
                     f"{min_humidity}", f"{avg_humidity}", f"{max_humidity}",
                     f"{rainfall:.0f}"]
        })
        st.dataframe(summary, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:20px; color:#666;">
    <p>Smart Precision Agriculture System | Built with Streamlit</p>
    <p style="font-size:0.8em;">Powered by Machine Learning | Data: Bangladesh Agricultural Dataset</p>
</div>
""", unsafe_allow_html=True)