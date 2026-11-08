from pathlib import Path
import pandas as pd
import xarray as xr
from hamsci_psws.io.digitalrf import read_digitalrf
from hamsci_psws.io.legacy.grape1 import read_grape_csv

def read_observation(data_path, **kwargs):
    """
    Unified reader that auto-detects legacy CSV files vs. DigitalRF data directories.
    """
    data_path = Path(data_path)
    if data_path.is_dir() or data_path.suffix in [".rf", ".hdf5", ".h5"]:
        return read_digitalrf(data_path, **kwargs)
    elif data_path.suffix == ".csv":
        return read_grape_csv(data_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format for path: {data_path}")