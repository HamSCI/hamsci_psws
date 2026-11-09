from pathlib import Path
from datetime import datetime
import numpy as np
import xarray as xr
import pandas as pd
import digital_rf as drf
import maidenhead as mh


def load_grape_drf_metadata(data_dir, channel="ch0") -> dict:
    """Extract metadata fields from a DigitalRF metadata directory."""
    data_dir_str = str(data_dir)
    meta_dir = f"{data_dir_str}/{channel}/metadata"
    dmr = drf.DigitalMetadataReader(meta_dir)
    do = drf.DigitalRFReader(data_dir_str)

    s0, s1 = do.get_bounds(channel)  #[cite: 3, 5]
    first_sample, _ = dmr.get_bounds()  #[cite: 3, 5]
    start_idx = int(np.uint64(first_sample))  #[cite: 3, 5]

    fields = dmr.get_fields()  #[cite: 3, 5]

    theCallsign = "Grape"
    if "callsign" in fields:  #[cite: 3]
        data_dict = dmr.read(start_idx, start_idx + 1, "callsign")  #[cite: 3]
        for key in data_dict.keys():
            theCallsign = data_dict[key].replace("/", "_")  #[cite: 3]
    elif "_" in channel:
        theCallsign = channel.partition("_")[2]  #[cite: 3]

    freqList = []
    if "center_frequencies" in fields:  #[cite: 3]
        data_dict = dmr.read(start_idx, start_idx + 1, "center_frequencies")  #[cite: 3]
        for key in data_dict.keys():
            freqList = [float(f) for f in data_dict[key]]  #[cite: 3, 6]

    theLatitude = 0.0
    if "lat" in fields:  #[cite: 3, 5]
        data_dict = dmr.read(start_idx, start_idx + 1, "lat")  #[cite: 3, 5]
        for key in data_dict.keys():
            theLatitude = float(data_dict[key])  #[cite: 3]

    theLongitude = 0.0
    if "long" in fields:  #[cite: 3, 5]
        data_dict = dmr.read(start_idx, start_idx + 1, "long")  #[cite: 3, 5]
        for key in data_dict.keys():
            theLongitude = float(data_dict[key])  #[cite: 3]

    if "grid_square" in fields:  #[cite: 3]
        data_dict = dmr.read(start_idx, start_idx + 1, "grid_square")  #[cite: 3]
        for key in data_dict.keys():
            theGridSquare = data_dict[key]  #[cite: 3]
    else:
        theGridSquare = mh.to_maiden(theLatitude, theLongitude)  #[cite: 3]

    props = do.get_properties(channel)  #[cite: 3, 5]
    fs = props["samples_per_second"]  #[cite: 3, 5]

    return {
        "callsign": theCallsign,
        "grid_square": theGridSquare,
        "latitude": theLatitude,
        "longitude": theLongitude,
        "center_frequencies": freqList,
        "sample_rate": fs,
        "s0": s0,
        "s1": s1,
    }


def read_digitalrf(
    data_dir: Path,
    channel: str = "ch0",
    start_sample: int = None,
    num_samples: int = None,
) -> xr.Dataset:
    """Reads DigitalRF directory metadata and continuous blocks into an xarray.Dataset."""
    data_dir_path = Path(data_dir)
    data_dir_str = str(data_dir_path)

    do = drf.DigitalRFReader(data_dir_str)
    meta_dir = data_dir_path / channel / "metadata"

    s0, s1 = do.get_bounds(channel)  #[cite: 3, 5]
    props = do.get_properties(channel)  #[cite: 3, 5]
    fs = props["samples_per_second"]  #[cite: 3, 5]

    freq_list = [0.0]
    lat, lon, callsign = 0.0, 0.0, "Unknown"

    if meta_dir.exists():
        dmr = drf.DigitalMetadataReader(str(meta_dir))  #[cite: 3, 5]
        first_sample, _ = dmr.get_bounds()  #[cite: 3, 5]
        start_idx = int(np.uint64(first_sample))  #[cite: 3, 5]
        meta_latest = dmr.read_latest()  #[cite: 5, 6]
        if meta_latest:
            latest_key = list(meta_latest.keys())[0]  #[cite: 5, 6]
            latest_meta = meta_latest[latest_key]  #[cite: 5, 6]
            if "center_frequencies" in latest_meta:
                freq_list = [float(f) for f in latest_meta["center_frequencies"]]  #[cite: 5, 6]
            if "lat" in latest_meta:
                lat = float(latest_meta["lat"])
            if "long" in latest_meta:
                lon = float(latest_meta["long"])
            if "callsign" in latest_meta:
                callsign = str(latest_meta["callsign"])

    s_start = s0 if start_sample is None else start_sample
    n_samps = (s1 - s0) if num_samples is None else num_samples

    # Pre-fill array with NaNs to keep data aligned across time gaps[cite: 4]
    raw_data = np.full((n_samps, len(freq_list)), np.nan, dtype=complex)  #[cite: 4]
    blocks = do.get_continuous_blocks(s_start, s_start + n_samps, channel)  #[cite: 4, 5, 6]

    for b_start, b_len in blocks.items():  #[cite: 4]
        lo = max(int(b_start), s_start)  #[cite: 4]
        hi = min(int(b_start) + int(b_len), s_start + n_samps)  #[cite: 4]
        if hi <= lo:
            continue
        chunk = do.read_vector(lo, hi - lo, channel)  #[cite: 4, 5, 6]

        # Handle 1D (single frequency) vs 2D (multi-frequency) arrays[cite: 6]
        if chunk.ndim == 1:  #[cite: 6]
            raw_data[lo - s_start : hi - s_start, 0] = chunk  #[cite: 6]
        else:
            raw_data[lo - s_start : hi - s_start, :] = chunk  #[cite: 6]

    time_utc = [drf.util.sample_to_datetime(s_start + i, fs) for i in range(n_samps)]  #[cite: 5, 6]

    return xr.Dataset(
        data_vars={"iq": (["time", "frequency"], raw_data)},
        coords={"time": time_utc, "frequency": freq_list},
        attrs={
            "sample_rate": fs,
            "latitude": lat,
            "longitude": lon,
            "callsign": callsign,
        },
    )