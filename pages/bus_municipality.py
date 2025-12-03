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

st.title("Autobuses por Municipio o Región")
st.write("Visualiza la posición de los autobuses de Bizkaibus filtrados por municipio o región.")

col1, col2 = st.columns(2)

stop_provincia, stop_municipio = get_unique_options(stops_bus, "DescripcionProvincia", "DescripcionMunicipio")

with col1:
    selected_municipio= st.multiselect("Municipio", options=stop_municipio,default=stop_municipio[0])
    ids_municipio = stops_bus[stops_bus["DescripcionMunicipio"].isin(selected_municipio)]["line_id"].unique().tolist()
with col2:
    selected_provincia = st.multiselect("Provincia", options=stop_provincia)
    ids_provincia = stops_bus[stops_bus["DescripcionProvincia"].isin(selected_provincia)]["line_id"].unique().tolist()
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

st.markdown("""
<style>
iframe {
    height: 100vh !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.components.v1.html(map_html, height=0, scrolling=False)