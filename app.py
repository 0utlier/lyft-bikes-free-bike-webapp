import folium
import requests
import streamlit as st
from folium.plugins import LocateControl
from streamlit_folium import st_folium

# ---- City settings: change CITY to switch systems ----
SYSTEMS = {
    "nyc": {"name": "Citi Bike", "code": "bkn", "center": (40.7306, -73.9866), "app": "citibike://"},
    "sf":  {"name": "Bay Wheels", "code": "bay", "center": (37.7749, -122.4194), "app": "baywheels://open"},
    "chi": {"name": "Divvy", "code": "chi", "center": (41.8781, -87.6298), "app": "divvybikes://"},
    "dc":  {"name": "Capital Bikeshare", "code": "dca", "center": (38.9072, -77.0369), "app": "capitalbikeshare://"},
}
CITY = "nyc"

SYSTEM = SYSTEMS[CITY]
FEED = f"https://gbfs.lyft.com/gbfs/1.1/{SYSTEM['code']}/en"

st.set_page_config(page_title="FreE-Bike Map", page_icon="🚲", layout="centered")

# Trim Streamlit chrome so the map gets the screen on a phone
st.markdown("""
<style>
  header, footer, #MainMenu {visibility: hidden;}
  .block-container {padding: 1rem 0.75rem 1rem;}
  .app-btn {display:block; text-align:center; padding:12px; margin-top:8px;
            background:#0A84FF; color:#fff !important; border-radius:10px;
            text-decoration:none; font-weight:600;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)  # GBFS refreshes about once a minute
def load_stations():
    info = requests.get(f"{FEED}/station_information.json", timeout=10).json()["data"]["stations"]
    status = requests.get(f"{FEED}/station_status.json", timeout=10).json()["data"]["stations"]
    status_by_id = {s["station_id"]: s for s in status}
    stations = []
    for s in info:
        stat = status_by_id.get(s["station_id"])
        if not stat or not stat.get("is_renting") or not stat.get("is_installed"):
            continue
        ebikes = stat.get("num_ebikes_available", 0)
        stations.append({
            "name": s["name"], "lat": s["lat"], "lon": s["lon"],
            "ebikes": ebikes,
            "classic": stat["num_bikes_available"] - ebikes,
        })
    return stations


st.markdown(f"### {SYSTEM['name']} FreE-Bike Map")

classic = st.number_input("Classic bikes at station", min_value=0, value=0, step=1,
                          help="0 = stations with ONLY e-bikes")

matches = [s for s in load_stations() if s["ebikes"] > 0 and s["classic"] == classic]
st.caption(f"{len(matches)} station{'' if len(matches) == 1 else 's'} · e-bikes + exactly {classic} classic")

m = folium.Map(location=SYSTEM["center"], zoom_start=14, tiles="OpenStreetMap",
               control_scale=True)
suffix = f" + {classic} classic" if classic else ""
for s in matches:
    folium.Marker(
        location=(s["lat"], s["lon"]),
        popup=folium.Popup(f"{s['name']}<br>({s['ebikes']} e-bikes{suffix})", max_width=300),
        icon=folium.Icon(color="blue", icon="bicycle", prefix="fa"),
    ).add_to(m)
LocateControl(auto_start=True, flyTo=True, keepCurrentZoomLevel=True).add_to(m)

st_folium(m, height=520, use_container_width=True, returned_objects=[])

st.markdown(f'<a class="app-btn" href="{SYSTEM["app"]}">🚲 Open {SYSTEM["name"]} app</a>',
            unsafe_allow_html=True)
