from google.transit import gtfs_realtime_pb2
import requests
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

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

def load_positions_bus(url,ns):
    resp_bus = requests.get(url)
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

    return pd.DataFrame(bus_rows)


# ======================================================
# 2) FETCH METRO DATA (GTFS-RT)
# ======================================================
def load_positions_metro(url):
    feed = gtfs_realtime_pb2.FeedMessage()
    resp_metro = requests.get(url)
    feed.ParseFromString(resp_metro.content)
    time_metro = datetime.fromtimestamp(feed.header.timestamp)

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
                "timestamp": time_metro,
                "mode": "metro"
            })

    return pd.DataFrame(metro_rows)
# ======================================================
# 3) FETCH RENFE DATA (GTFS-RT)
# ======================================================
def load_positions_renfe(url):

    feed = gtfs_realtime_pb2.FeedMessage()
    resp_renfe = requests.get(url)
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
                "timestamp": datetime.fromtimestamp(vp.timestamp) if vp.timestamp else None,
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
    return df_renfe