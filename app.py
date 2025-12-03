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
st.title("Bizkaia Public Transport Live Map (🚍🚇🚆)")
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

st.components.v1.html(map_html, height=500, scrolling=False)


# ======================================================
# 7) Filters testing 
# ======================================================
st.title("Playing with filters (🚍)")
# -----------------------------
# 7.1. Filter by line name
# -----------------------------
st.header("Stations")

with st.expander("Filter by Line Name", expanded=False):
    col1, col2 = st.columns(2)

    line_ids, line_names = get_unique_options(lines_bus, "line_id", "DenominacionLinea")

    with col1:
        selected_ids = st.multiselect("Line ID", options=line_ids)
    with col2:
        selected_names = st.multiselect("Line Name", options=line_names)

    all_selected_ids, _ = sync_selection(lines_bus, selected_ids, selected_names, "line_id", "DenominacionLinea")

    # Filter DataFrames
    selected_lines,selected_stops,vehicles_bus_filtered = filter_datasets_by_lines(
        lines_bus,stops_bus,df_bus,all_selected_ids
    )

    # Create map
    map_html = create_filtered_map(
        lines_gdf=selected_lines,
        stops_gdf=selected_stops,
        vehicles_df=vehicles_bus_filtered,
        lines_tooltip_cols=["line_id"],
        stops_popup_col="Denominacion",
        vehicles_popup_cols=[]
    )

    st.components.v1.html(map_html, height=600, scrolling=False)
    
# -----------------------------
# 7.2. Filter by Municipality
# -----------------------------

st.header("Municipalities")

with st.expander("Filter by Municipality or Regions", expanded=False):
    col1, col2 = st.columns(2)

    stop_provincia, stop_municipio = get_unique_options(stops_bus, "DescripcionProvincia", "DescripcionMunicipio")

    with col1:
        selected_provincia = st.multiselect("DescripcionProvincia", options=stop_provincia)
        ids_provincia = stops_bus[stops_bus["DescripcionProvincia"].isin(selected_provincia)]["line_id"].unique().tolist()
    with col2:
        selected_municipio= st.multiselect("DescripcionMunicipio", options=stop_municipio)
        ids_municipio = stops_bus[stops_bus["DescripcionMunicipio"].isin(selected_municipio)]["line_id"].unique().tolist()
    all_selected_ids = list(dict.fromkeys(ids_provincia + ids_municipio))

    # Filter DataFrames
    selected_lines,selected_stops,vehicles_bus_filtered = filter_datasets_by_lines(
        lines_bus,stops_bus,df_bus,all_selected_ids
    )

    # Create map
    map_html = create_filtered_map(
        lines_gdf=selected_lines,
        stops_gdf=selected_stops,
        vehicles_df=vehicles_bus_filtered,
        lines_tooltip_cols=["line_id"],
        stops_popup_col="Denominacion",
        vehicles_popup_cols=[]
    )

    st.components.v1.html(map_html, height=600, scrolling=False)

# -----------------------------
# 7.3. Filter by Active
# -----------------------------

st.header("Active buses")

with st.expander("Filter by Lines with Active Buses", expanded=False):

    all_selected_ids = df_bus["line_id"].unique().tolist()
    
    # Filter DataFrames
    selected_lines,selected_stops,vehicles_bus_filtered = filter_datasets_by_lines(
        lines_bus,stops_bus,df_bus,all_selected_ids
    )

    # Create map
    map_html = create_filtered_map(
        lines_gdf=selected_lines,
        stops_gdf=selected_stops,
        vehicles_df=vehicles_bus_filtered,
        lines_tooltip_cols=["line_id"],
        stops_popup_col="Denominacion",
        vehicles_popup_cols=[]
    )

    st.components.v1.html(map_html, height=600, scrolling=False)


# -----------------------------
# 6.2 Map of only bus content
# -----------------------------


# st.title("🚍 Super heavy map BizkaiaBus")
# with st.expander("Kill my browser by adding all bus lines, stops and vehicles!"):
#     # Make map with lines & stops & Buses
#     map_html = create_stops_lines_folium_map(
#         lines_gdf=lines_bus,
#         stops_gdf=stops_bus,
#         vehicles_df=df_bus,
#         lines_group_col="layer_name",
#         lines_tooltip_cols=["line_id"],
#         stops_popup_col="Denominacion",
#         vehicles_popup_cols=["vehicle_id", "mode", "timestamp"]
#     )

#     st.components.v1.html(map_html, height=600, scrolling=False)

# -----------------------------
# 6.3 Version with tiles
# -----------------------------
# import streamlit as st
# import folium
# from pathlib import Path
# import socket
# import http.server, socketserver, threading

# st.title("🚍 BizkaiaBus map with vector tiles")

# OUTPUT_TILES_DIR = PROCESSED_DATA_DIR / "tiles"

# # Pick a free port dynamically
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind(("", 0))
# PORT = s.getsockname()[1]
# s.close()

# # Start a lightweight HTTP server
# class ReusableTCPServer(socketserver.TCPServer):
#     allow_reuse_address = True

# handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(PROCESSED_DATA_DIR), **kwargs)
# httpd = ReusableTCPServer(("", PORT), handler)
# threading.Thread(target=httpd.serve_forever, daemon=True).start()
# st.write(f"Serving tiles at http://localhost:{PORT}/tiles/")

# # Folium map
# m = folium.Map(location=[43.2630, -2.9350], zoom_start=11, tiles="CartoDB Positron")

# # Add all line layers
# # line_types = ["BizkaibusLine1", "BizkaibusLine2", "BizkaibusLine3", "BizkaibusLine4"]
# # for line_type in line_types:
# #     folium.TileLayer(
# #         tiles=f"http://localhost:{PORT}/tiles/lines_{line_type}/{{z}}/{{x}}/{{y}}.mvt",
# #         attr=f"Lines {line_type}",
# #         name=f"Bus {line_type}",
# #         overlay=True,
# #         control=True,
# #         tms=True
# #     ).add_to(m)

# # Optional: add stops
# folium.TileLayer(
#     tiles=f"http://localhost:{PORT}/tiles/stops/{{z}}/{{x}}/{{y}}.mvt",
#     attr="Stops",
#     name="Stops",
#     overlay=True,
#     control=True,
#     tms=True
# ).add_to(m)

# # Layer control
# folium.LayerControl().add_to(m)

# # Render in Streamlit
# st.components.v1.html(m._repr_html_(), height=600, scrolling=False)
