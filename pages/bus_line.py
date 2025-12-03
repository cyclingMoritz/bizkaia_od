import streamlit as st
import geopandas as gpd

from src.vehicles import load_positions_bus
from src.maps import create_filtered_map
from src.filtering_menus import get_unique_options, sync_selection, filter_datasets_by_lines
from src.config import PROCESSED_DATA_DIR

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
# 1) Filters and Map
# ======================================================

st.title("Autobuses por Línea")
st.write("Visualiza la posición de los autobuses de Bizkaibus filtrados por línea.")

# filter UI + map here
col1, col2 = st.columns(2)

line_ids, line_names = get_unique_options(lines_bus, "line_id", "DenominacionLinea")

with col1:
    selected_names = st.multiselect("Line Name", options=line_names, default=line_names[0])
with col2:
    selected_ids = st.multiselect("Line ID", options=line_ids)

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

st.markdown("""
<style>
iframe {
    height: 100vh !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.components.v1.html(map_html, height=0, scrolling=False)