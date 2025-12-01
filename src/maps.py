import folium
import geopandas as gpd

import folium
import geopandas as gpd
import pandas as pd

def create_stops_lines_folium_map(
    lines_gdf: gpd.GeoDataFrame,
    stops_gdf: gpd.GeoDataFrame,
    vehicles_df: pd.DataFrame = None,
    lines_group_col: str = "layer_name",
    lines_tooltip_cols: list = ["CodigoLinea"],
    stops_popup_col: str = "Denominacion",
    vehicles_popup_cols: list = ["vehicle_id", "mode", "timestamp"],
    map_center: tuple = (43.2630, -2.9350),
    zoom_start: int = 11,
    line_color: str = "green",
    line_weight: int = 3,
    line_opacity: float = 0.7,
    stop_color: str = "blue",
    stop_fill_color: str = "lightblue",
    stop_radius: int = 4,
    stop_opacity: float = 0.8,
    vehicle_color: str = "red",
    vehicle_fill_color: str = "orange",
    vehicle_radius: int = 5,
    vehicle_opacity: float = 0.9
) -> str:
    """
    Create a Folium map with bus lines, stops, and optionally vehicles.
    Returns HTML string for Streamlit.
    """
    
    # Ensure WGS84
    lines_gdf = lines_gdf.to_crs(epsg=4326)
    stops_gdf = stops_gdf.to_crs(epsg=4326)
    
    # Convert datetime columns to string to avoid JSON serialization errors
    for df in [lines_gdf, stops_gdf]:
        datetime_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
        for col in datetime_cols:
            df[col] = df[col].astype(str)
    
    # Create Folium map
    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles="CartoDB Positron")
    
    # Add bus lines split by layer
    for layer_name, group in lines_gdf.groupby(lines_group_col):
        fg = folium.FeatureGroup(name=f"Line: {layer_name}", show=False)
        folium.GeoJson(
            group.__geo_interface__,
            style_function=lambda x, c=line_color, w=line_weight, o=line_opacity: {
                'color': c,
                'weight': w,
                'opacity': o
            },
            tooltip=folium.GeoJsonTooltip(fields=lines_tooltip_cols)
        ).add_to(fg)
        fg.add_to(m)
    
    # Add bus stops
    fg_stops = folium.FeatureGroup(name="Bus Stops", show=True)
    for _, stop in stops_gdf.iterrows():
        folium.CircleMarker(
            [stop.geometry.y, stop.geometry.x],
            radius=stop_radius,
            color=stop_color,
            fill=True,
            fill_color=stop_fill_color,
            fill_opacity=stop_opacity,
            popup=stop.get(stops_popup_col, "Bus Stop")
        ).add_to(fg_stops)
    fg_stops.add_to(m)
    
    # Add vehicles if provided
    if vehicles_df is not None and not vehicles_df.empty:
        fg_vehicles = folium.FeatureGroup(name="Vehicles", show=True)
        # Convert timestamp to string if exists
        if "timestamp" in vehicles_df.columns:
            vehicles_df["timestamp"] = vehicles_df["timestamp"].astype(str)
        
        for _, vehicle in vehicles_df.iterrows():
            popup_text = "<br>".join(f"{col}: {vehicle.get(col, '')}" for col in vehicles_popup_cols if col in vehicle)
            folium.CircleMarker(
                [vehicle['lat'], vehicle['lon']],
                radius=vehicle_radius,
                color=vehicle_color,
                fill=True,
                fill_color=vehicle_fill_color,
                fill_opacity=vehicle_opacity,
                popup=popup_text
            ).add_to(fg_vehicles)
        fg_vehicles.add_to(m)
    
    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    return m._repr_html_()
