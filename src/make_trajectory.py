import geopandas as gpd
from shapely.geometry import LineString
from pathlib import Path
import pandas as pd
from config import RAW_DATA_DIR as INPUT
from config import PROCESSED_DATA_DIR as OUTPUT


# 1️⃣ Read all GPKG files in order
files = sorted(INPUT.glob("bizkaibus_*.gpkg"))

gdfs = []
for f in files:
    gdf = gpd.read_file(f)
    # Keep only essential columns
    gdf = gdf[["vehicle_ref", "journey_ref", "stop_ref", "recorded_at", "geometry"]]
    gdfs.append(gdf)

# 2️⃣ Combine all snapshots
all_vehicles = pd.concat(gdfs, ignore_index=True)
all_vehicles["recorded_at"] = pd.to_datetime(all_vehicles["recorded_at"])

# 3️⃣ Optional: sort by vehicle and time
all_vehicles = all_vehicles.sort_values(["vehicle_ref", "recorded_at"])

# 4️⃣ Convert back to GeoDataFrame
all_vehicles_gdf = gpd.GeoDataFrame(all_vehicles, geometry="geometry", crs="EPSG:4326")

# 5️⃣ Create trajectories per vehicle (LineString)
trajectories = []
for vehicle, group in all_vehicles_gdf.groupby("vehicle_ref"):
    # Only keep vehicles with at least 2 points
    if len(group) >= 2:
        line = LineString(group.geometry.tolist())
        traj = {
            "vehicle_ref": vehicle,
            "journey_ref": group["journey_ref"].iloc[0],
            "stop_ref": group["stop_ref"].iloc[0],
            "start_time": group["recorded_at"].min(),
            "end_time": group["recorded_at"].max(),
            "geometry": line
        }
        trajectories.append(traj)

traj_gdf = gpd.GeoDataFrame(trajectories, geometry="geometry", crs="EPSG:4326")

# 6️⃣ Save trajectories to a single GPKG
traj_gdf.to_file(OUTPUT / "bizkaibus_trajectories.gpkg", driver="GPKG")

print(f"Created {len(traj_gdf)} vehicle trajectories")
