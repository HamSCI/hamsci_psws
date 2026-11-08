import pandas as pd
import requests
import plotly.express as px
from pathlib import Path

def query_inventory(
    start_date: str, 
    end_date: str, 
    station_id: str = None, 
    lat_range: tuple = None, 
    lon_range: tuple = None, 
    frequency: float = None, 
    instrument_id: int = None
) -> pd.DataFrame:
    """Queries PSWS data inventory and returns standardized DataFrame metadata."""
    base_url = "https://pswsnetwork.eng.ua.edu/observations/downloadapi/" #
    params = {"start_date": start_date, "end_date": end_date} #[cite: 1]
    
    if station_id:
        params["station_id"] = station_id #[cite: 1]
    elif lat_range and lon_range:
        params["lat_min"], params["lat_max"] = lat_range #[cite: 1]
        params["lon_min"], params["lon_max"] = lon_range #[cite: 1]
        
    if frequency is not None:
        params["frequency"] = frequency #[cite: 1]
    if instrument_id is not None:
        params["instrument_id"] = instrument_id #[cite: 1]

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    
    # Standardize JSON response to DataFrame
    df = pd.DataFrame(response.json())
    df["start_time"] = pd.to_datetime(df["start_date"]) #[cite: 2]
    df["end_time"] = pd.to_datetime(df["end_date"]) #[cite: 2]
    return df

def plot_inventory_gantt(inventory_df: pd.DataFrame, output_html: Path = Path("inventory_gantt.html")):
    """Generates an interactive HTML Gantt chart of data availability across stations."""
    fig = px.timeline(
        inventory_df, 
        x_start="start_time", 
        x_end="end_time", 
        y="station_id", 
        color="instrument_type", #[cite: 2]
        hover_data=["frequency", "data_type"], #[cite: 2]
        title="PSWS Observation Inventory"
    )
    fig.update_yaxes(autorange="reversed")
    fig.write_html(str(output_html))
    return fig

import zipfile

def download_dataset(inventory_df: pd.DataFrame, target_dir: Path, unpack: bool = True) -> list[Path]:
    """Downloads dataset ZIP archives and optionally extracts DigitalRF directories."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    downloaded_paths = []

    for _, row in inventory_df.iterrows():
        # URL construction from observation ID or direct API link
        download_url = f"https://pswsnetwork.eng.ua.edu/observations/download_range/{row['id']}/" #[cite: 2]
        zip_path = target_dir / f"{row['station_id']}_{row['id']}.zip" #[cite: 2]
        
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        if unpack and zipfile.is_zipfile(zip_path):
            extract_dir = target_dir / f"{row['station_id']}_{row['id']}" #[cite: 2]
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            zip_path.unlink()
            downloaded_paths.append(extract_dir)
        else:
            downloaded_paths.append(zip_path)

    return downloaded_paths
