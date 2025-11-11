import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_geolocation import st_geolocation

# ===========================
# KONFIGURASI DASAR
# ===========================
st.set_page_config(
    page_title="🌦️ Prakiraan Cuaca Indonesia",
    page_icon="🌤️",
    layout="centered"
)

# Ganti API key kamu di sini (dari https://openweathermap.org/api)
OWM_API_KEY = "MASUKKAN_API_KEY_KAMU_DI_SINI"

# Lokasi default: Polewali
DEFAULT_CITY = "Polewali"
DEFAULT_LAT, DEFAULT_LON = -3.4328, 119.3435


# ===========================
# HELPER FUNCTION
# ===========================
def get_weather_by_city(city):
    """Ambil data cuaca saat ini berdasarkan nama kota."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=id"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Gagal memuat cuaca untuk {city}: {e}")
        return None


def get_forecast_by_city(city):
    """Ambil prakiraan 5 hari berdasarkan nama kota."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OWM_API_KEY}&units=metric&lang=id"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.warning(f"Gagal memuat prakiraan: {e}")
        return None


def reverse_geocode(lat, lon):
    """Ubah koordinat jadi nama kota."""
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        data = requests.get(geo_url).json()
        address = data.get("address", {})
        return (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or DEFAULT_CITY
        )
    except:
        return DEFAULT_CITY


# ===========================
# DETEKSI LOKASI OTOMATIS
# ===========================
st.title("🌍 Aplikasi Prakiraan Cuaca Real-Time")
st.markdown("#### Deteksi lokasi otomatis menggunakan GPS browser Anda")

loc = st_geolocation(key="geoloc")

if loc and loc.get("latitude") and loc.get("longitude"):
    lat, lon = loc["latitude"], loc["longitude"]
    city = reverse_geocode(lat, lon)
    st.success(f"📍 Lokasi terdeteksi: **{city}** ({lat:.4f}, {lon:.4f})")
else:
    st.info("📍 Menggunakan lokasi default: **Polewali**")
    lat, lon, city = DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY


# ===========================
# PENCARIAN KOTA MANUAL
# ===========================
st.markdown("### 🔎 Cari Kota Lain (Opsional)")
manual_city = st.text_input("Masukkan nama kota:", "")

if manual_city:
    city = manual_city


# ===========================
# AMBIL DATA CUACA
# ===========================
weather = get_weather_by_city(city)
forecast = get_forecast_by_city(city)

if weather:
    st.subheader(f"🌤️ Cuaca Saat Ini di {city}")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Suhu", f"{weather['main']['temp']} °C")
        st.metric("Kelembapan", f"{weather['main']['humidity']} %")
        st.metric("Tekanan Udara", f"{weather['main']['pressure']} hPa")

    with col2:
        st.metric("Kecepatan Angin", f"{weather['wind']['speed']} m/s")
        st.metric("Awan", f"{weather['clouds']['all']} %")
        st.metric("Kondisi", weather['weather'][0]['description'].capitalize())
        icon = weather['weather'][0]['icon']
        st.image(f"https://openweathermap.org/img/wn/{icon}@2x.png")

# ===========================
# GRAFIK PRAKIRAAN
# ===========================
if forecast:
    st.subheader("📈 Prakiraan Cuaca 5 Hari ke Depan")
    df = pd.DataFrame([
        {"Waktu": item["dt_txt"], "Suhu (°C)": item["main"]["temp"]}
        for item in forecast["list"]
    ])
    fig = px.line(df, x="Waktu", y="Suhu (°C)", title=f"Perkiraan Suhu Harian di {city}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Tidak dapat memuat data prakiraan cuaca.")

st.caption("Data cuaca: OpenWeatherMap.org | Lokasi: OpenStreetMap | Aplikasi oleh ChatGPT + Kamu 🌦️")
