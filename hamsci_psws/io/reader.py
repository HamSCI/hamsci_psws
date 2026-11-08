from pathlib import Path
from hamsci_psws.io.digitalrf import read_digitalrf
from hamsci_psws.io.legacy.grape1 import read_grape_csv


def read_observation(data_path, **kwargs):
    """
    Unified reader that auto-detects legacy CSV files vs DigitalRF directories.
    """
    data_path = Path(data_path)

    # 1. Direct CSV file
    if data_path.suffix == ".csv":
        return read_grape_csv(data_path, **kwargs)

    # 2. Direct DigitalRF directory or RF data file
    if data_path.is_dir() or data_path.suffix in [".rf", ".hdf5", ".h5"]:
        return read_digitalrf(data_path, **kwargs)

    # 3. Sub-file inside a DigitalRF observation folder (e.g., gap_summary.json)
    if data_path.is_file() and data_path.parent.is_dir():
        parent_dir = data_path.parent
        has_drf_structure = (
            (parent_dir / "ch0").exists()
            or (parent_dir / "metadata").exists()
            or any(parent_dir.glob("*.h5"))
            or any(parent_dir.glob("*/*.h5"))
        )
        if has_drf_structure:
            return read_digitalrf(parent_dir, **kwargs)

    raise ValueError(f"Unsupported file format for path: {data_path}")