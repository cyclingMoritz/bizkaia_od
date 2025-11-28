import requests
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point
import pytz
from pathlib import Path
from config import RAW_DATA_DIR

URL = "https://ctb-siri.s3.eu-south-2.amazonaws.com/bizkaibus-vehicle-positions.xml"
DATA_DIR = RAW_DATA_DIR

def fetch_xml(url: str) -> str:
    """Download the raw XML."""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text


def parse_vehicle_positions(xml_text: str):
    """
    Parse SIRI-VM and return:
      - GeoDataFrame with vehicle positions
      - dataset_timestamp (newest RecordedAtTime)
    """
    root = ET.fromstring(xml_text)

    ns = {"s": "http://www.siri.org.uk/siri"}  # SIRI namespaces

    activities = root.findall(".//s:VehicleActivity", ns)

    rows = []
    timestamps = []

    for act in activities:
        recorded_at = act.findtext("s:RecordedAtTime", namespaces=ns)
        timestamps.append(recorded_at)

        mvj = act.find("s:MonitoredVehicleJourney", ns)
        if mvj is None:
            continue

        lat = mvj.findtext("s:VehicleLocation/s:Latitude", namespaces=ns)
        lon = mvj.findtext("s:VehicleLocation/s:Longitude", namespaces=ns)
        veh_ref = mvj.findtext("s:VehicleRef", namespaces=ns)
        journey_ref = mvj.findtext("s:VehicleJourneyRef", namespaces=ns)
        stop_ref = mvj.findtext("s:MonitoredCall/s:StopPointRef", namespaces=ns)

        if lat and lon:
            rows.append({
                "vehicle_ref": veh_ref,
                "journey_ref": journey_ref,
                "stop_ref": stop_ref,
                "lat": float(lat),
                "lon": float(lon),
                "recorded_at": recorded_at
            })

    # dataset timestamp = newest RecordedAtTime
    if timestamps:
        dataset_timestamp = max(timestamps)
    else:
        dataset_timestamp = None

    # Build GeoDataFrame
    gdf = gpd.GeoDataFrame(
        rows,
        geometry=[Point(r["lon"], r["lat"]) for r in rows],
        crs="EPSG:4326"
    )

    return gdf, dataset_timestamp


def save_snapshot(gdf, timestamp_str: str):
    """Save GeoDataFrame as a GeoPackage named with the dataset timestamp."""
    # Normalize timestamp for filenames
    t = datetime.fromisoformat(timestamp_str)
    normalized = t.strftime("%Y%m%d_%H%M%S")

    out_path = DATA_DIR / f"bizkaibus_{normalized}.gpkg"

    gdf.to_file(out_path)

    # Store metadata inside GPKG
    gdf.set_crs("EPSG:4326", inplace=True)
    print(f"Saved snapshot → {out_path}")


def loop_fetch(interval_seconds=10):
    """Continuously fetch and store only new versions."""
    last_timestamp = None
    print(f"Starting Bizkaibus fetch loop (every {interval_seconds}s)...")

    while True:
        try:
            xml_text = fetch_xml(URL)
            gdf, ts = parse_vehicle_positions(xml_text)

            if ts is None:
                print("⚠️  No timestamp found → skipping.")
            else:
                if ts != last_timestamp:
                    print(f"✔️  New dataset detected: {ts}")
                    save_snapshot(gdf, ts)
                    last_timestamp = ts
                else:
                    print(f"⏳ No new data (timestamp unchanged: {ts})")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(interval_seconds)
# ---------------------------------------------------------
# Run
# ---------------------------------------------------------
if __name__ == "__main__":
    loop_fetch(interval_seconds=10)