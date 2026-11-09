from pathlib import Path
import io
import re
import zipfile
import logging
import pandas as pd
import requests

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

logger = logging.getLogger("hamsci_psws.client.rest")


def _query_single_window(
    start_date: str,
    end_date: str,
    station_id: str = None,
    lat_range: tuple = None,
    lon_range: tuple = None,
    frequency: float = None,
    instrument_id: int = None,
    base_url: str = "https://pswsnetwork.eng.ua.edu/observations/downloadapi/",
    timeout: int = 30,
) -> pd.DataFrame:
    params = {"start_date": start_date, "end_date": end_date}
    if station_id:
        params["station_id"] = station_id
    elif lat_range and lon_range:
        params["lat_min"], params["lat_max"] = lat_range
        params["lon_min"], params["lon_max"] = lon_range

    if frequency is not None:
        params["frequency"] = frequency
    if instrument_id is not None:
        params["instrument_id"] = instrument_id

    response = requests.get(base_url, params=params, timeout=timeout)

    if response.status_code == 404:
        return pd.DataFrame()

    if response.status_code == 400:
        raise requests.HTTPError(f"400 Bad Request: {response.text}", response=response)

    if response.status_code == 429:
        raise requests.HTTPError("429 Rate limit exceeded (100 requests/day limit reached).", response=response)

    response.raise_for_status()

    try:
        z = zipfile.ZipFile(io.BytesIO(response.content))
        file_list = z.namelist()
    except zipfile.BadZipFile as e:
        raise ValueError(f"PSWS API returned invalid non-ZIP response: {e}")

    records = []
    obs_groups = {}
    for fname in file_list:
        parts = fname.strip("/").split("/")
        if len(parts) >= 2 and parts[0].startswith("S"):
            st_id = parts[0]
            obs_name = parts[1]
            group_key = f"{st_id}/{obs_name}"
        else:
            group_key = parts[0]

        if group_key not in obs_groups:
            obs_groups[group_key] = []
        obs_groups[group_key].append(fname)

    for group_key, group_files in obs_groups.items():
        match_dt = re.search(r"(\d{4}-\d{2}-\d{2})T?(\d{2})?[-:]?(\d{2})?", group_key)
        if match_dt:
            date_str = match_dt.group(1)
            hr_str = match_dt.group(2) or "00"
            mn_str = match_dt.group(3) or "00"
            s_time = pd.to_datetime(f"{date_str} {hr_str}:{mn_str}:00")
            e_time = s_time + pd.Timedelta(days=1)
        else:
            s_time = pd.to_datetime(start_date)
            e_time = pd.to_datetime(end_date)

        match_st = re.search(r"(S\d{6}|N\d+)", group_key)
        st_id = match_st.group(1) if match_st else (station_id or "Unknown")

        if any("metadata" in f or ".h5" in f for f in group_files):
            inst_type = "rx888"
            data_type = "spectrum"
        elif any(f.endswith(".csv") for f in group_files):
            inst_type = "grape_v1"
            data_type = "doppler_csv"
        else:
            inst_type = "raw"
            data_type = "binary"

        records.append(
            {
                "id": group_key,
                "station_id": st_id,
                "instrument_type": inst_type,
                "data_type": data_type,
                "frequency": frequency if frequency is not None else 10.0,
                "start_date": str(s_time),
                "end_date": str(e_time),
                "start_time": s_time,
                "end_time": e_time,
                "zip_files": group_files,
            }
        )

    return pd.DataFrame(records)


def query_inventory(
    start_date: str,
    end_date: str,
    station_id: str = None,
    lat_range: tuple = None,
    lon_range: tuple = None,
    frequency: float = None,
    instrument_id: int = None,
    base_url: str = "https://pswsnetwork.eng.ua.edu/observations/downloadapi/",
    chunk_days: int = 7,
    timeout: int = 30,
) -> pd.DataFrame:
    """Queries PSWS inventory with automatic bisection on 500 MB limit and live tqdm progress."""
    s_dt = pd.to_datetime(start_date)
    e_dt = pd.to_datetime(end_date)

    if s_dt >= e_dt:
        e_dt = s_dt + pd.Timedelta(days=1)

    total_days = (e_dt - s_dt).days

    try:
        if total_days <= chunk_days:
            return _query_single_window(
                start_date, end_date, station_id, lat_range, lon_range, frequency, instrument_id, base_url, timeout
            )
    except requests.HTTPError as err:
        if err.response is not None and err.response.status_code == 400:
            mid_days = max(1, total_days // 2)
            mid_dt = s_dt + pd.Timedelta(days=mid_days)
            df1 = query_inventory(
                start_date, mid_dt.strftime("%Y-%m-%d"), station_id, lat_range, lon_range,
                frequency, instrument_id, base_url, max(1, chunk_days // 2), timeout
            )
            df2 = query_inventory(
                (mid_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), end_date, station_id, lat_range, lon_range,
                frequency, instrument_id, base_url, max(1, chunk_days // 2), timeout
            )
            return pd.concat([df1, df2], ignore_index=True).drop_duplicates(subset=["id"])
        else:
            raise

    # Build sub-windows list
    date_windows = []
    curr_start = s_dt
    while curr_start < e_dt:
        curr_end = min(curr_start + pd.Timedelta(days=chunk_days), e_dt)
        date_windows.append((curr_start.strftime("%Y-%m-%d"), curr_end.strftime("%Y-%m-%d")))
        curr_start = curr_end + pd.Timedelta(days=1)

    sub_dfs = []
    for s_str, e_str in tqdm(date_windows, desc="Querying PSWS Inventory", unit="window"):
        try:
            df_chunk = query_inventory(
                s_str, e_str, station_id, lat_range, lon_range, frequency, instrument_id, base_url, chunk_days, timeout
            )
            if not df_chunk.empty:
                sub_dfs.append(df_chunk)
        except Exception as e:
            logger.error(f"Failed querying chunk {s_str} to {e_str}: {e}")

    if not sub_dfs:
        return pd.DataFrame(
            columns=[
                "id", "station_id", "instrument_type", "data_type",
                "frequency", "start_date", "end_date", "start_time", "end_time"
            ]
        )

    return pd.concat(sub_dfs, ignore_index=True).drop_duplicates(subset=["id"])


def download_dataset(
    inventory_df: pd.DataFrame = None,
    target_dir: Path = Path("./data"),
    unpack: bool = True,
    start_date: str = None,
    end_date: str = None,
    station_id: str = None,
    frequency: float = None,
    base_url: str = "https://pswsnetwork.eng.ua.edu/observations/downloadapi/",
    timeout: int = 120,
) -> list[Path]:
    """Downloads dataset archives from PSWS API and returns top-level observation folders/files."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if inventory_df is not None and not inventory_df.empty:
        s_date = start_date or str(inventory_df["start_time"].min().date())
        e_date = end_date or str(inventory_df["end_time"].max().date())
        st_id = station_id or (inventory_df["station_id"].iloc[0] if "station_id" in inventory_df else None)
        freq = frequency or (inventory_df["frequency"].iloc[0] if "frequency" in inventory_df else None)
    else:
        s_date = start_date
        e_date = end_date
        st_id = station_id
        freq = frequency

    params = {"start_date": s_date, "end_date": e_date}
    if st_id:
        params["station_id"] = st_id
    if freq:
        params["frequency"] = freq

    response = requests.get(base_url, params=params, stream=True, timeout=timeout)
    response.raise_for_status()

    zip_filename = f"psws_{st_id or 'dataset'}_{s_date}_to_{e_date}.zip"
    zip_path = target_dir / zip_filename

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    if unpack:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(target_dir)
                extracted_names = zf.namelist()

            # Group extracted items by top-level root folder/file
            root_items = set()
            for name in extracted_names:
                top_name = name.strip("/").split("/")[0]
                root_path = target_dir / top_name
                if root_path.exists():
                    root_items.add(root_path)

            zip_path.unlink()
            return sorted(list(root_items))
        except zipfile.BadZipFile as e:
            logger.error(f"Failed to unpack ZIP archive at {zip_path}: {e}")
            raise
    else:
        return [zip_path]