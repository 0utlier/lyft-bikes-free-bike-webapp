import time

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
STALE_AFTER = 30 * 60  # ignore stations that haven't reported in 30 min (frozen counts)

SYSTEM = SYSTEMS[CITY]
FEED = f"https://gbfs.lyft.com/gbfs/2.3/{SYSTEM['code']}/en"

st.set_page_config(page_title="FreE-Bike Map", page_icon="🚲", layout="centered")

st.markdown("""
<style>
  header, footer, #MainMenu {display: none !important;}
  .block-container {padding: 0.5rem 0.5rem 0 !important;}
  /* keep the counter + app button on one row on phones */
  [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 0.5rem !important;}
  [data-testid="stColumn"] {min-width: 0 !important;}
  .app-btn {display:flex; align-items:center; justify-content:center; height:2.5rem;
            background:#0A84FF; color:#fff !important; border-radius:8px;
            text-decoration:none; font-size:0.85rem; font-weight:600; white-space:nowrap;}
</style>
""", unsafe_allow_html=True)


def get(name):
    return requests.get(f"{FEED}/{name}.json", timeout=10).json()["data"]


@st.cache_data(ttl=30)
def load_stations():
    info = get("station_information")["stations"]
    status = {s["station_id"]: s for s in get("station_status")["stations"]}
    classic_types = {v["vehicle_type_id"] for v in get("vehicle_types")["vehicle_types"]
                     if v.get("propulsion_type") == "human"}
    now = time.time()

    stations = []
    for s in info:
        stat = status.get(s["station_id"])
        if (not stat or not stat.get("is_renting") or not stat.get("is_installed")
                or now - stat.get("last_reported", 0) > STALE_AFTER):
            continue
        types = stat.get("vehicle_types_available")
        if types:  # count classics directly instead of total minus e-bikes
            classic = sum(t["count"] for t in types if t["vehicle_type_id"] in classic_types)
            ebikes = sum(t["count"] for t in types if t["vehicle_type_id"] not in classic_types)
        else:
            ebikes = stat.get("num_ebikes_available", 0)
            classic = stat["num_bikes_available"] - ebikes
        stations.append({"name": s["name"], "lat": s["lat"], "lon": s["lon"],
                         "ebikes": ebikes, "classic": classic})
    return stations


left, right = st.columns([2, 1], vertical_alignment="center")
with left:
    classic = st.number_input("Classic bikes", min_value=0, value=0, step=1,
                              label_visibility="collapsed")
with right:
    st.markdown(f'<a class="app-btn" href="{SYSTEM["app"]}">Open app</a>', unsafe_allow_html=True)

matches = [s for s in load_stations() if s["ebikes"] > 0 and s["classic"] == classic]

m = folium.Map(location=SYSTEM["center"], zoom_start=14, tiles="OpenStreetMap")
suffix = f" + {classic} classic" if classic else ""
for s in matches:
    folium.Marker(
        location=(s["lat"], s["lon"]),
        popup=folium.Popup(f"{s['name']}<br>({s['ebikes']} e-bikes{suffix})", max_width=300),
        icon=folium.Icon(color="blue", icon="bicycle", prefix="fa"),
    ).add_to(m)
LocateControl(auto_start=True, flyTo=True, keepCurrentZoomLevel=True).add_to(m)

st_folium(m, height=600, use_container_width=True, returned_objects=[])
