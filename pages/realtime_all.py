import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import datetime
import folium
import time


from src.vehicles import load_positions_bus,load_positions_metro, load_positions_renfe
from src.maps import create_stops_lines_folium_map, plot_vehicles_by_mode, create_filtered_map
from src.filtering_menus import get_unique_options, sync_selection, filter_datasets_by_lines
from src.config import PROCESSED_DATA_DIR
st.set_page_config(page_title="Bizkaia Public Transport", layout="wide")

REFRESH_INTERVAL = 60  # seconds




# ======================================================
# 1) FETCH BUS DATA (SIRI XML)
# ======================================================

BUS_URL = "https://ctb-siri.s3.eu-south-2.amazonaws.com/bizkaibus-vehicle-positions.xml"
ns = {"siri": "http://www.siri.org.uk/siri"}

# Load data
df_bus = load_positions_bus(BUS_URL,ns)
lines_bus = gpd.read_file(PROCESSED_DATA_DIR / "Bizkaibus" / "bizkaibus_lines.gpkg", layer="lines")
stops_bus = gpd.read_file(PROCESSED_DATA_DIR / "Bizkaibus" / "bizkaibus_stops.gpkg", layer="stops")





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
st.title("Transporte público de Bizkaia en tiempo real (🚍🚇🚆)")
st.write(
    "Visualizamos datos en tiempo real de diferentes tipos de vehículos: autobuses (Bizkaibus), metro (Metro Bilbao) y trenes (Renfe). "
    "Las posiciones y estados de los vehículos se actualizan aproximadamente cada 2 minutos."
)
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
# -----------------------------
# 6.1. General map with all vehicles by mode
# -----------------------------

df_all = pd.concat([df_bus, df_metro, df_renfe], ignore_index=True, sort=False)

map_html = plot_vehicles_by_mode(
    df_vehicles=df_all,
    mode_colors={'bus':'green','metro':'orange','renfe':'purple'},
    radius=6
)

st.markdown("""
<style>
iframe {
    height: 100vh !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.components.v1.html(map_html, height=0, scrolling=False)