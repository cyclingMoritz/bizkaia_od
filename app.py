import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from google.transit import gtfs_realtime_pb2
import time


from realtime.vehicles import load_positions_bus,load_positions_metro, load_positions_renfe

st.set_page_config(page_title="Bizkaia Public Transport", layout="wide")

REFRESH_INTERVAL = 60  # seconds
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

df_bus = load_positions_bus(BUS_URL,ns)


# ======================================================
# 2) FETCH METRO DATA (GTFS-RT)
# ======================================================
METRO_URL = "https://ctb-gtfs-rt.s3.eu-south-2.amazonaws.com/metro-bilbao-vehicle-positions.pb"

df_metro = load_positions_metro(METRO_URL)


# ======================================================
# 3) FETCH RENFE DATA (GTFS-RT)
# ======================================================
RENFE_URL = "https://gtfsrt.renfe.com/vehicle_positions.pb"

df_renfe = load_positions_renfe(RENFE_URL)


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
    st.rerun()



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
m = folium.Map(location=[43.2630, -2.9350], zoom_start=11,tiles="CartoDB Positron")

# HTML circle icon
def icon(color):
    return f'<span style="color:{color}; font-size:20px;">●</span>'

# Define layer groups
layer_bus = folium.FeatureGroup(name=f"{icon('green')} Bus", show=True)
layer_metro = folium.FeatureGroup(name=f"{icon('orange')} Metro", show=True)
layer_renfe = folium.FeatureGroup(name=f"{icon('purple')} Renfe", show=True)

layer_bus.add_to(m)
layer_metro.add_to(m)
layer_renfe.add_to(m)

# -----------------------------
# 3. Add each marker to its group
# -----------------------------
for _, row in df_all.iterrows():
    mode = row.get("mode", None)

    # safety check
    if mode not in ("bus", "metro", "renfe"):
        continue
    
    # pick layer
    if mode == "bus":
        layer = layer_bus
        color = "green"
    elif mode == "metro":
        layer = layer_metro
        color = "orange"
    elif mode == "renfe":
        layer = layer_renfe
        color = "purple"
    else:
        layer = layer_renfe
        color = "blue"

    # popup
    popup = f"{mode.upper()} — {row.get('vehicle_id')}"

    # create marker
    folium.CircleMarker(
        [row["lat"], row["lon"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        popup=popup
    ).add_to(layer)

folium.LayerControl(overlay=True).add_to(m)



# st_folium(m, width=700, height=500)

map_html = m._repr_html_()   # produces <iframe> with full map
st.components.v1.html(map_html, height=500, scrolling=False)


