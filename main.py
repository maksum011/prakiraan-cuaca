import streamlit as st
import requests
import datetime
import time
import pandas as pd
import plotly.express as px

# ======================
# CONFIGURASI DASAR
# ======================
st.set_page_config(page_title="🌦️ Prakiraan Cuaca", page_icon="🌤️", layout="centered")

OWM_API_KEY = "648469f28a0f56ca8c8b52d00db2ac8a"  # <-- ganti dengan API key kamu sendiri
DEFAULT_UNITS = "metric"  # metric = Celcius

# ======================
# GAYA DAN HEADER
# ======================
st.markdown("""
    <style>
    body {
        background: linear-gradient(to bottom, #e0f7fa, #ffffff);
        color: #004d66;
    }
    .main-title {
        text-align:center; 
        font-size:2.2em; 
        font-weight:700; 
        color:#0077b6;
        margin-bottom:0.2em;
    }
    .sub-title {
        text-align:center; 
        font-size:1.1em; 
        color:#555;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🌦️ Prakiraan Cuaca Terkini</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Aplikasi pendeteksi cuaca otomatis dengan lokasi GPS</div>", unsafe_allow_html=True)
st.write("")

# ======================
# DETEKSI LOKASI (GPS via streamlit-javascript + MANUAL SEARCH)
# ======================
st.markdown("### 📍 Deteksi Lokasi Pengguna")

def get_gps_location_via_js():
    """Gunakan JS untuk mendapatkan lokasi GPS tanpa reload halaman"""
    try:
        from streamlit_javascript import st_javascript
    except Exception:
        return {"error": "streamlit_javascript_not_installed"}

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
        { enableHighAccuracy: true, maximumAge: 0, timeout: 7000 }
      );
    });
    """

    try:
        # ⚠️ Hilangkan argumen 'timeout' (tidak diperlukan di versi sekarang)
        result = st_javascript(js, key="get_gps_location")
        return result or {"error": "no_response"}
    except Exception as e:
        return {"error": f"st_javascript_error: {e}"}



# -------------- main logic --------------
lat = lon = None
city = None

# 1️⃣ Coba deteksi lokasi via GPS browser
gps_result = get_gps_location_via_js(timeout_ms=7000)

if gps_result.get("error"):
    err = gps_result["error"]
    if err == "streamlit_javascript_not_installed":
        st.info("📦 Untuk deteksi GPS otomatis, install paket `streamlit-javascript`.")
    else:
        st.warning(f"⚠️ GPS error: {err}")
else:
    lat = gps_result.get("lat")
    lon = gps_result.get("lon")
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        geo = requests.get(geo_url, timeout=6).json()
        address = geo.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
            or address.get("state")
        )
        city = city or "Lokasi tidak diketahui"
        st.success(f"📍 Lokasi GPS terdeteksi: **{city}** ({lat:.4f}, {lon:.4f})")
    except Exception as e:
        st.warning(f"⚠️ Gagal membaca data lokasi: {e}")

# 2️⃣ Fallback: pencarian manual
st.markdown("### 🔍 Cari Kota Manual (atau cari kota lain)")

city_input = st.text_input("Masukkan nama kota:", value=city or "")

if st.button("Cari Kota Ini"):
    if city_input.strip() == "":
        st.warning("Masukkan nama kota terlebih dahulu.")
    else:
        try:
            geo_api = f"https://api.openweathermap.org/geo/1.0/direct?q={city_input}&limit=1&appid={OWM_API_KEY}"
            geo_data = requests.get(geo_api, timeout=6).json()
            if isinstance(geo_data, list) and len(geo_data) > 0:
                lat = geo_data[0]["lat"]
                lon = geo_data[0]["lon"]
                city = geo_data[0].get("name") or city_input
                st.success(f"📍 Lokasi manual: **{city}** ({lat:.4f}, {lon:.4f})")
            else:
                st.error("Kota tidak ditemukan. Coba ejaan lain.")
        except Exception as e:
            st.error(f"Gagal mencari kota: {e}")

# 3️⃣ Jika masih belum dapat lokasi, fallback ke Polewali
if not lat or not lon:
    lat, lon, city = -3.4329, 119.3435, "Polewali"
    st.info(f"📍 Menggunakan lokasi default: **{city}** ({lat:.4f}, {lon:.4f})")


# ======================
# AMBIL DATA CUACA (Free API)
# ======================
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={DEFAULT_UNITS}&appid={OWM_API_KEY}&lang=id"
        res = requests.get(url)
        data = res.json()
        if res.status_code != 200:
            st.error("Gagal memuat data cuaca: " + data.get("message", "Tidak diketahui"))
            return None
        return data
    except Exception as e:
        st.error(f"Gagal memuat data cuaca: {e}")
        return None

weather = get_weather(lat, lon)

# ======================
# TAMPILKAN CUACA SAAT INI
# ======================
if weather:
    st.subheader(f"🌤️ Cuaca Saat Ini di {city}")
    col1, col2 = st.columns(2)
    with col1:
        st.image(f"https://openweathermap.org/img/wn/{weather['weather'][0]['icon']}@2x.png")
        st.markdown(f"**{weather['weather'][0]['description'].capitalize()}**")
    with col2:
        st.metric("Suhu", f"{weather['main']['temp']} °C")
        st.metric("Kelembapan", f"{weather['main']['humidity']}%")
        st.metric("Tekanan Udara", f"{weather['main']['pressure']} hPa")

    st.divider()

    # Informasi tambahan
    st.write("🌬️ **Kecepatan Angin:**", f"{weather['wind']['speed']} m/s")
    st.write("☁️ **Awan:**", f"{weather['clouds']['all']}%")
    st.write("🌡️ **Suhu Maksimum:**", f"{weather['main']['temp_max']} °C")
    st.write("🌡️ **Suhu Minimum:**", f"{weather['main']['temp_min']} °C")
    st.write("🌅 **Terbit:**", datetime.datetime.fromtimestamp(weather['sys']['sunrise']).strftime('%H:%M'))
    st.write("🌇 **Terbenam:**", datetime.datetime.fromtimestamp(weather['sys']['sunset']).strftime('%H:%M'))

# ======================
# PRAKIRAAN (5 HARI)
# ======================
def get_forecast(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units={DEFAULT_UNITS}&appid={OWM_API_KEY}&lang=id"
        res = requests.get(url)
        data = res.json()
        if res.status_code != 200:
            st.warning("Tidak dapat memuat data prakiraan: " + data.get("message", ""))
            return None
        return data
    except:
        return None

forecast = get_forecast(lat, lon)

if forecast:
    st.subheader("📅 Prakiraan Cuaca 5 Hari ke Depan")
    df = pd.DataFrame([{
        "Waktu": item["dt_txt"],
        "Suhu (°C)": item["main"]["temp"],
        "Kelembapan (%)": item["main"]["humidity"],
        "Cuaca": item["weather"][0]["description"]
    } for item in forecast["list"]])

    fig = px.line(df, x="Waktu", y="Suhu (°C)", title="Perkiraan Suhu Harian")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df[["Waktu", "Suhu (°C)", "Kelembapan (%)", "Cuaca"]])

# ======================
# CATATAN
# ======================
st.info("💡 Data diperoleh dari OpenWeatherMap (Free API) dan lokasi otomatis dari GPS browser.")






