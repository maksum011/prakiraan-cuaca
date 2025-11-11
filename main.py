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
# DETEKSI LOKASI (GPS + MANUAL SEARCH)
# ======================
st.markdown("### 📍 Deteksi Lokasi Pengguna")

def get_gps_location():
    """Minta lokasi pengguna via GPS (JavaScript)"""
    js = """
    <script>
    function sendLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    const coords = `${lat},${lon}`;
                    const url = new URL(window.location.href);
                    url.searchParams.set('coords', coords);
                    window.location.href = url.toString();
                },
                (err) => {
                    const url = new URL(window.location.href);
                    url.searchParams.set('error', err.message);
                    window.location.href = url.toString();
                },
                {enableHighAccuracy: true, timeout: 5000}
            );
        } else {
            const url = new URL(window.location.href);
            url.searchParams.set('error', 'Browser tidak mendukung GPS');
            window.location.href = url.toString();
        }
    }
    sendLocation();
    </script>
    """
    st.components.v1.html(js, height=0)

# Inisialisasi variabel
lat, lon, city = None, None, None

# Jalankan deteksi GPS
get_gps_location()
time.sleep(1)

# Ambil parameter dari URL (pakai API baru Streamlit)
params = st.query_params

if "coords" in params:
    try:
        lat, lon = map(float, params["coords"].split(","))
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        geo = requests.get(geo_url).json()
        city = geo.get("address", {}).get("city", "Lokasi tidak diketahui")
        st.success(f"📍 Lokasi terdeteksi: **{city}** ({lat:.2f}, {lon:.2f})")
    except Exception as e:
        st.warning(f"⚠️ Gagal membaca data GPS: {e}")
elif "error" in params:
    st.warning(f"⚠️ Gagal mendeteksi lokasi GPS: {params['error']}")
else:
    st.info("Silakan izinkan akses lokasi (Allow Location) di browser Anda.")
    
# ======================
# FITUR PENCARIAN KOTA MANUAL
# ======================
st.markdown("### 🔍 Cari Kota Lainnya")

city_input = st.text_input("Masukkan nama kota (contoh: Surabaya, Bandung, Medan):", value=city or "")

if st.button("Cari Cuaca Kota Ini"):
    if city_input.strip() == "":
        st.warning("Masukkan nama kota terlebih dahulu.")
    else:
        try:
            geo_api = f"https://api.openweathermap.org/geo/1.0/direct?q={city_input}&limit=1&appid={OWM_API_KEY}"
            geo_data = requests.get(geo_api).json()
            if len(geo_data) == 0:
                st.error("Kota tidak ditemukan. Coba nama lain.")
            else:
                lat = geo_data[0]["lat"]
                lon = geo_data[0]["lon"]
                city = geo_data[0]["name"]
                st.success(f"📍 Lokasi manual: **{city}** ({lat:.2f}, {lon:.2f})")
        except Exception as e:
            st.error(f"Gagal mencari kota: {e}")

# Jika tetap tidak ada lokasi, fallback ke Jakarta
if not lat or not lon:
    lat, lon, city = -3.404667, 119.305695, "Polewali"
    st.info("📍 Menggunakan lokasi default: Polewali")

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




