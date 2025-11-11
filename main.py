import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_javascript import st_javascript

# ======================
# KONFIGURASI DASAR
# ======================
st.set_page_config(page_title="🌦️ Prakiraan Cuaca", page_icon="🌤️", layout="centered")

OWM_API_KEY = "648469f28a0f56ca8c8b52d00db2ac8a"  # ganti dengan API gratis OWM kamu
DEFAULT_CITY = "Polewali"
DEFAULT_LAT, DEFAULT_LON = -3.4329, 119.3435

st.title("🌦️ Aplikasi Pendeteksi Cuaca BMKG Style")
st.caption("Menampilkan cuaca real-time & prakiraan 5 hari ke depan dengan lokasi otomatis GPS.")


# ======================
# DETEKSI LOKASI GPS
# ======================
def get_gps_location():
    """Minta lokasi pengguna via JavaScript (tanpa reload)"""
    js = """
    new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve({ error: "Browser tidak mendukung geolocation" });
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude });
            },
            (err) => {
                resolve({ error: err.message });
            },
            { enableHighAccuracy: true, timeout: 7000 }
        );
    });
    """
    try:
        return st_javascript(js, key="get_gps")
    except Exception as e:
        return {"error": str(e)}


def reverse_geocode(lat, lon):
    """Ubah koordinat menjadi nama kota"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        data = requests.get(url, timeout=5).json()
        addr = data.get("address", {})
        return addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or "Lokasi tidak diketahui"
    except:
        return "Lokasi tidak diketahui"


# ======================
# PENGAMBILAN DATA CUACA
# ======================
def get_weather(lat, lon):
    """Ambil data cuaca dari API gratis (current + forecast)"""
    try:
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OWM_API_KEY}"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OWM_API_KEY}"

        current = requests.get(current_url).json()
        forecast = requests.get(forecast_url).json()
        return current, forecast
    except Exception as e:
        st.error(f"Gagal memuat data cuaca: {e}")
        return None, None


# ======================
# UI LOKASI (GPS + MANUAL)
# ======================
st.subheader("📍 Deteksi Lokasi")

gps = get_gps_location()
lat, lon, city = None, None, None

if gps and not gps.get("error"):
    lat, lon = gps.get("lat"), gps.get("lon")
    city = reverse_geocode(lat, lon)
    st.success(f"📍 Lokasi GPS terdeteksi: **{city}** ({lat:.2f}, {lon:.2f})")
else:
    if gps.get("error"):
        st.warning(f"⚠️ Tidak dapat mendeteksi GPS: {gps['error']}")
    st.info(f"📍 Menggunakan lokasi default: **{DEFAULT_CITY}**")
    lat, lon, city = DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY

# Input pencarian kota manual
st.text_input("🔎 Cari kota lain:", key="manual_city")
if st.session_state.manual_city:
    q = st.session_state.manual_city
    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={q}&limit=1&appid={OWM_API_KEY}"
    res = requests.get(geo_url).json()
    if res:
        lat, lon, city = res[0]["lat"], res[0]["lon"], res[0]["name"]
        st.success(f"📍 Lokasi manual: **{city}** ({lat:.2f}, {lon:.2f})")
    else:
        st.error("Kota tidak ditemukan.")


# ======================
# TAMPILKAN DATA CUACA
# ======================
current, forecast = get_weather(lat, lon)
if not current:
    st.stop()

try:
    st.markdown("---")
    st.markdown(f"## 🌤️ Cuaca Sekarang di **{city}**")

    temp = current["main"]["temp"]
    desc = current["weather"][0]["description"].capitalize()
    icon = current["weather"][0]["icon"]
    humidity = current["main"]["humidity"]
    wind = current["wind"]["speed"]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(f"https://openweathermap.org/img/wn/{icon}@2x.png", width=100)
    with col2:
        st.metric("Suhu", f"{temp:.1f}°C")
        st.metric("Kelembapan", f"{humidity}%")
        st.metric("Kecepatan Angin", f"{wind} m/s")

    # ======================
    # GRAFIK PRAKIRAAN 5 HARI
    # ======================
    st.markdown("---")
    st.subheader("📊 Prakiraan 5 Hari ke Depan")

    df = pd.DataFrame([
        {
            "Waktu": datetime.fromtimestamp(item["dt"]),
            "Suhu (°C)": item["main"]["temp"],
            "Cuaca": item["weather"][0]["description"].capitalize()
        }
        for item in forecast["list"]
    ])

    fig = px.line(df, x="Waktu", y="Suhu (°C)", title="Perkiraan Suhu Harian", markers=True)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Gagal memproses data cuaca: {e}")

st.markdown("---")
st.caption("💧 Data cuaca oleh OpenWeatherMap (Free API) • Desain ala BMKG by ChatGPT")
