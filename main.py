import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import time

# ===========================
# KONFIGURASI DASAR
# ===========================
st.set_page_config(page_title="🌦️ Prakiraan Cuaca", page_icon="🌤️", layout="centered")

API_KEY = "648469f28a0f56ca8c8b52d00db2ac8a"  # OpenWeatherMap free API
DEFAULT_CITY = "Polewali"
DEFAULT_LAT, DEFAULT_LON = -3.4328, 119.3435


# ===========================
# JAVASCRIPT UNTUK GPS
# ===========================
def get_user_location():
    js_code = """
    <script>
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const coords = pos.coords.latitude + "," + pos.coords.longitude;
            const search = new URLSearchParams(window.location.search);
            search.set("coords", coords);
            window.location.search = search.toString();
        },
        (err) => {
            const search = new URLSearchParams(window.location.search);
            search.set("error", err.message);
            window.location.search = search.toString();
        },
        {enableHighAccuracy: true, timeout: 5000}
    );
    </script>
    """
    components.html(js_code, height=0, width=0)


# ===========================
# REVERSE GEOCODE KE NAMA KOTA
# ===========================
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        geo = requests.get(url, headers={"User-Agent": "streamlit-weather"}).json()
        return geo.get("address", {}).get("city", DEFAULT_CITY)
    except Exception:
        return DEFAULT_CITY


# ===========================
# FUNGSI PENGAMBIL CUACA (API GRATIS)
# ===========================
def get_weather(city, api_key=API_KEY):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=id"
        res = requests.get(url)
        data = res.json()

        if res.status_code != 200 or "main" not in data:
            raise Exception(data.get("message", "Gagal mengambil data cuaca."))

        info = {
            "Kota": data["name"],
            "Suhu": f"{data['main']['temp']} °C",
            "Kelembapan": f"{data['main']['humidity']}%",
            "Tekanan": f"{data['main']['pressure']} hPa",
            "Kecepatan Angin": f"{data['wind']['speed']} m/s",
            "Deskripsi": data["weather"][0]["description"].capitalize(),
            "Ikon": data["weather"][0]["icon"],
        }
        return info
    except Exception as e:
        st.error(f"⚠️ {e}")
        return None


# ===========================
# APLIKASI UTAMA
# ===========================
st.title("🌦️ Prakiraan Cuaca Real-Time")
st.write("Aplikasi prakiraan cuaca otomatis mendeteksi lokasi GPS atau bisa cari manual.")

st.divider()

params = st.query_params
lat, lon, city = None, None, DEFAULT_CITY

if "coords" in params:
    try:
        lat, lon = map(float, params["coords"].split(","))
        city = reverse_geocode(lat, lon)
        st.success(f"📍 Lokasi terdeteksi otomatis: **{city}** ({lat:.2f}, {lon:.2f})")
    except:
        st.warning("⚠️ Gagal membaca data GPS, gunakan pencarian manual.")
elif "error" in params:
    st.warning(f"⚠️ Gagal mendeteksi GPS: {params['error']}")
else:
    get_user_location()
    st.info("🛰️ Mohon izinkan akses lokasi di browser Anda...")
    st.stop()

# Input manual kota
st.divider()
manual_city = st.text_input("🔍 Atau masukkan nama kota:", city)
if manual_city:
    city = manual_city

# ===========================
# TAMPILKAN DATA CUACA
# ===========================
weather = get_weather(city)
if weather:
    st.markdown(f"## 🌤️ Cuaca di **{weather['Kota']}**")
    st.image(f"https://openweathermap.org/img/wn/{weather['Ikon']}@2x.png", width=100)
    st.write(f"**{weather['Deskripsi']}**")
    st.metric("🌡️ Suhu", weather["Suhu"])
    st.metric("💧 Kelembapan", weather["Kelembapan"])
    st.metric("🌬️ Kecepatan Angin", weather["Kecepatan Angin"])
    st.metric("📊 Tekanan Udara", weather["Tekanan"])

st.caption("Data diperoleh dari OpenWeatherMap API (versi gratis).")
