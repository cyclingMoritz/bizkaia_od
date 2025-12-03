import streamlit as st
from streamlit import Page
from src.config import PAGES_DIR

st.set_page_config(
    page_title="Bizkaia Public Transport", 
    layout="wide")

# --- Streamlit pages ---
realtime_all = Page(f"{PAGES_DIR}/realtime_all.py", title="Todos los vehículos")
bus_line = Page(f"{PAGES_DIR}/bus_line.py", title="Bus por línea")
bus_muni = Page(f"{PAGES_DIR}/bus_municipality.py", title="Bus por municipio")
bus_active = Page(f"{PAGES_DIR}/bus_active.py", title="Buses activos")

pg = st.navigation(
    {
        "Vehículos en tiempo real": [realtime_all],
        "Buses": [bus_line, bus_muni, bus_active]
    },
    position="sidebar"  # "sidebar" or top bar depending on your plugin
)

pg.run()
