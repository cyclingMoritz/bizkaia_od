import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from google.transit import gtfs_realtime_pb2
import time
REFRESH_INTERVAL = 60  # seconds

# ---------------------------------------------
# Utils
# ---------------------------------------------
def parse_iso8601(ts):
    """Convert ISO8601 timestamp string → datetime."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except:
        return None


# ======================================================
# 1) FETCH BUS DATA (SIRI XML)
# ======================================================
BUS_URL = "https://ctb-siri.s3.eu-south-2.amazonaws.com/bizkaibus-vehicle-positions.xml"
ns = {"siri": "http://www.siri.org.uk/siri"}

resp_bus = requests.get(BUS_URL)
resp_bus.raise_for_status()
root = ET.fromstring(resp_bus.content)

bus_rows = []

for activity in root.findall(".//siri:VehicleActivity", ns):
    mvj = activity.find(".//siri:MonitoredVehicleJourney", ns)
    if mvj is None:
        continue

    loc = mvj.find(".//siri:VehicleLocation", ns)
    if loc is None:
        continue

    lat = loc.find("siri:Latitude", ns)
    lon = loc.find("siri:Longitude", ns)
    if lat is None or lon is None:
        continue

    vehicle_id = mvj.findtext("siri:VehicleRef", default=None, namespaces=ns)
    timestamp = activity.findtext("siri:RecordedAtTime", default=None, namespaces=ns)

    bus_rows.append({
        "vehicle_id": vehicle_id,
        "lat": float(lat.text),
        "lon": float(lon.text),
        "timestamp": parse_iso8601(timestamp),
        "mode": "bus"
    })

df_bus = pd.DataFrame(bus_rows)


# ======================================================
# 2) FETCH METRO DATA (GTFS-RT)
# ======================================================
METRO_URL = "https://ctb-gtfs-rt.s3.eu-south-2.amazonaws.com/metro-bilbao-vehicle-positions.pb"

feed = gtfs_realtime_pb2.FeedMessage()
resp_metro = requests.get(METRO_URL)
feed.ParseFromString(resp_metro.content)

metro_rows = []
for ent in feed.entity:
    if ent.HasField("vehicle"):
        vp = ent.vehicle
        pos = vp.position
        if pos.latitude is None or pos.longitude is None:
            continue
        metro_rows.append({
            "vehicle_id": vp.vehicle.id if vp.vehicle.id else None,
            "lat": pos.latitude,
            "lon": pos.longitude,
            "timestamp": datetime.utcfromtimestamp(vp.timestamp) if vp.timestamp else None,
            "mode": "metro"
        })

df_metro = pd.DataFrame(metro_rows)


# ======================================================
# 3) FETCH RENFE DATA (GTFS-RT)
# ======================================================
RENFE_URL = "https://gtfsrt.renfe.com/vehicle_positions.pb"

feed = gtfs_realtime_pb2.FeedMessage()
resp_renfe = requests.get(RENFE_URL)
feed.ParseFromString(resp_renfe.content)

renfe_rows = []
for ent in feed.entity:
    if ent.HasField("vehicle"):
        vp = ent.vehicle
        pos = vp.position
        if pos.latitude is None or pos.longitude is None:
            continue
        renfe_rows.append({
            "vehicle_id": vp.vehicle.id if vp.vehicle.id else None,
            "lat": pos.latitude,
            "lon": pos.longitude,
            "timestamp": datetime.utcfromtimestamp(vp.timestamp) if vp.timestamp else None,
            "mode": "renfe"
        })

df_renfe = pd.DataFrame(renfe_rows)

# Optional: filter by Bizkaia bounding box
min_lon, max_lon = -3.5, -2.3
min_lat, max_lat = 43.0, 43.5
df_renfe = df_renfe[
    (df_renfe.lon >= min_lon) & (df_renfe.lon <= max_lon) &
    (df_renfe.lat >= min_lat) & (df_renfe.lat <= max_lat)
].reset_index(drop=True)


# ======================================================
# 4) AUTOREFRESH SETUP
# ======================================================


if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Compute seconds until next refresh
remaining = int(REFRESH_INTERVAL - (time.time() - st.session_state.last_refresh))
if remaining <= 0:
    # Time to refresh
    st.session_state.last_refresh = time.time()
    st.experimental_rerun()

# Show countdown
st.write(f"⏱️ Next update in: {remaining} s")


# ======================================================
# 5) INFO PANELS
# ======================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🚍 Bizkaibus (SIRI)")
    st.write(f"**Vehicles detected:** {len(df_bus)}")
    if len(df_bus) > 0 and df_bus['timestamp'].notna().any():
        last_bus = df_bus['timestamp'].max()
        st.write("**Last update:**", last_bus.strftime("%d %b %Y, %H:%M:%S"))
with col2:
    st.subheader("🚇 Metro Bilbao (GTFS-RT)")
    st.write(f"**Vehicles detected:** {len(df_metro)}")
    if len(df_metro) > 0 and df_metro['timestamp'].notna().any():
        last_metro = df_metro['timestamp'].max()
        st.write("**Last update:**", last_metro.strftime("%d %b %Y, %H:%M:%S"))
with col3:
    st.subheader("🚆 Renfe Trains (Bizkaia)")
    st.write(f"**Vehicles detected:** {len(df_renfe)}")
    if len(df_renfe) > 0 and df_renfe['timestamp'].notna().any():
        st.write("**Last update:**", df_renfe['timestamp'].max().strftime("%d %b %Y, %H:%M:%S"))



# ======================================================
# 6) COMBINE & MAP
# ======================================================
df_all = pd.concat([df_bus, df_metro, df_renfe], ignore_index=True, sort=False)
# Center map on Bilbao
m = folium.Map(location=[43.2630, -2.9350], zoom_start=11)

for _, row in df_all.iterrows():
    if row["mode"] == "bus":
        color = "blue"
    elif row["mode"] == "metro":
        color = "red"
    else:  # renfe
        color = "green"
    popup = f"{row['mode'].upper()} — {row['vehicle_id']}"
    folium.CircleMarker(
        [row["lat"], row["lon"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        popup=popup
    ).add_to(m)


st_folium(m, width=700, height=500)
