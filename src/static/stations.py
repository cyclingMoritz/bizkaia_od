import pandas as pd
import zipfile
import io
import requests


def load_metro_stations(gtfs_zip_url):
    # download GTFS zip
    resp = requests.get(gtfs_zip_url)
    z = zipfile.ZipFile(io.BytesIO(resp.content))

    stops = pd.read_csv(z.open("stops.txt"))

    df = stops.rename(columns={
        "stop_id": "station_id",
        "stop_name": "name",
        "stop_lat": "lat",
        "stop_lon": "lon"
    })[["station_id", "name", "lat", "lon"]]

    df["mode"] = "metro"

    return df