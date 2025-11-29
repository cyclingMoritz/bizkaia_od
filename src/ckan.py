import requests
import pandas as pd

def fetch_catalog(API_URL):
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    # Lista completa de paquetes
    packages = data["result"]

    # Aplanamos los datasets en un DataFrame
    rows = []
    for p in packages:
        for r in p.get("resources", []):
            rows.append({
                "dataset_id": p.get("id"),
                "dataset_name": p.get("name"),
                "dataset_title": p.get("title"),
                "notes": p.get("notes"),
                "organization": p.get("organization", {}).get("title"),
                "resource_id": r.get("id"),
                "resource_name": r.get("name"),
                "resource_format": r.get("format"),
                "resource_url": r.get("url"),
                "resource_last_modified": r.get("last_modified"),
            })
    df = pd.DataFrame(rows)
    return df