import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px

# ===========================
# KONFIGURASI DASAR
# ===========================
st.set_page_config(page_title="🌦️ Prakiraan Cuaca", page_icon="🌤️", layout="centered")

OWM_API_KEY = "648469f28a0f56ca8c8b52d00db2ac8a"  # API gratis dari OpenWeatherMap
DEFAULT_CITY = "Polewali"
DEFAULT_LAT, DEFAULT_LON = -3.4328, 119.3435

# ===========================
# HELPER FUNCTION
# ===========================
def get_weather(city):
    """Ambil data cuaca berdasarkan nama kota (pakai API gratis OWM)."""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=id"
    r = requests.get(url)
    if r.status_code != 200:
        st.error("❌ Gagal memuat data cuaca. Periksa API key atau nama kota.")
        return None
    return r.json()

def get_forecast(city):
    """Ambil prakiraan 5 hari (tiap 3 jam)."""
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OWM_API_KEY}&units=metric&lang=id"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def reverse_geocode(lat, lon):
    """Ubah koordinat jadi nama kota."""
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        data = requests.get(geo_url).json()
        return data.get("address", {}).get("city") or data.get("address", {}).get("town") or data.get("address", {}).get("village", DEFAULT_CITY)
    except:
        return DEFAULT_CITY

# ===========================
# DETEKSI LOKASI GPS
# ===========================
def get_gps_location():
    """Ambil lokasi pengguna via browser (JavaScript)."""
    js = """
    <script>
    function sendCoords() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const coords = pos.coords.latitude + "," + pos.coords.longitude;
                    const input = window.parent.document.querySelector('input[data-testid="stTextInput-input"]');
                    input.value = coords;
                    input.dispatchEvent(new Event("input", { bubbles: true }));
                },
                (err) => {
                    const input = window.parent.document.querySelector('input[data-testid="stTextInput-input"]');
                    input.value = "ERROR:" + err.message;
                    input.dispatchEvent(new Event("input", { bubbles: true }));
                },
                { enableHighAccuracy: true, timeout: 7000 }
            );
        } else {
            const input = window.parent.document.querySelector('input[data-testid="stTextInput-input"]');
            input.value = "ERROR:Browser tidak mendukung GPS";
            input.dispatchEvent(new Event("input", { bubbles: true }));
        }
    }
    sendCoords();
    </script>
    """
    coords = st.text_input("Koordinat GPS (otomatis)")
    st.components.v1.html(js, height=0)
    if coords.startswith("ERROR:"):
        return {"error": coords[6:]}
    elif "," in coords:
        lat, lon = map(float, coords.split(","))
        return {"lat": lat, "lon": lon}
    return {}

# ===========================
# UI: DETEKSI LOKASI
# ===========================
st.header("🌍 Deteksi Lokasi & Prakiraan Cuaca")
gps = get_gps_location()

if isinstance(gps, dict) and gps.get("lat") and gps.get("lon"):
    lat, lon = gps["lat"], gps["lon"]
    city = reverse_geocode(lat, lon)
    st.success(f"📍 Lokasi GPS terdeteksi: **{city}** ({lat:.2f}, {lon:.2f})")
elif isinstance(gps, dict) and gps.get("error"):
    st.warning(f"⚠️ Gagal mendeteksi lokasi GPS: {gps['error']}")
    city, lat, lon = DEFAULT_CITY, DEFAULT_LAT, DEFAULT_LON
    st.info(f"📍 Menggunakan lokasi default: **{DEFAULT_CITY}**")
else:
    city, lat, lon = DEFAULT_CITY, DEFAULT_LAT, DEFAULT_LON
    st.info(f"📍 Menggunakan lokasi default: **{DEFAULT_CITY}**")

# ===========================
# PENCARIAN KOTA
# ===========================
st.markdown("### 🔎 Cari Kota Lain")
manual_city = st.text_input("Masukkan nama kota (contoh: Jakarta, Surabaya, Polewali):", "")
if manual_city:
    city = manual_city

# ===========================
# AMBIL DATA CUACA
# ===========================
weather = get_weather(city)
forecast = get_forecast(city)

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
    st.subheader("📈 Prakiraan 5 Hari ke Depan")
    df = pd.DataFrame([
        {"Waktu": item["dt_txt"], "Suhu (°C)": item["main"]["temp"]}
        for item in forecast["list"]
    ])
    fig = px.line(df, x="Waktu", y="Suhu (°C)", title=f"Perkiraan Suhu Harian di {city}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Tidak dapat memuat data prakiraan cuaca.")

st.caption("Data cuaca: OpenWeatherMap.org | Lokasi: OpenStreetMap | Aplikasi oleh ChatGPT + Kamu 🌦️")
