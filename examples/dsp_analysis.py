import logging
from pathlib import Path
from hamsci_psws import read_observation
from hamsci_psws.analysis.spectrum import compute_doppler_psd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("dsp_analysis")


def discover_observations(data_dir: Path) -> list[Path]:
    """Recursively scans data_dir for valid DigitalRF folders or Grape CSV files."""
    data_dir = Path(data_dir)
    found_paths = []

    for p in data_dir.rglob("*"):
        if p.is_dir():
            if (
                (p / "ch0").exists()
                or (p / "metadata").exists()
                or (p / "gap_summary.json").exists()
                or any(p.glob("*.h5"))
            ):
                if not any(p.is_relative_to(parent) for parent in found_paths):
                    found_paths.append(p)
        elif p.is_file() and p.suffix == ".csv":
            if not any(p.is_relative_to(parent) for parent in found_paths):
                found_paths.append(p)

    return found_paths


def main():
    data_dir = Path("./data")

    if not data_dir.exists():
        print(f"Data directory {data_dir.resolve()} does not exist. Run quickstart_psws.py first.")
        return

    obs_candidates = discover_observations(data_dir)

    if not obs_candidates:
        print(f"No observation folders or CSV files found in {data_dir.resolve()}. Run quickstart_psws.py first.")
        return

    obs_target = obs_candidates[0]
    print(f"\nFound {len(obs_candidates)} observation(s) in {data_dir.resolve()}.")
    print(f"Auto-selected target for DSP analysis: {obs_target.resolve()}")

    dataset = read_observation(obs_target)

    if hasattr(dataset, "attrs"):
        freq = dataset.coords["frequency"].values[0]
        iq_data = dataset.sel(frequency=freq)["iq"].values.squeeze()
        sample_rate = dataset.attrs["sample_rate"]

        frequencies, spec_times, Sxx_db = compute_doppler_psd(
            iq_data=iq_data,
            sample_rate=sample_rate,
            nfft=1024,
            window="hann",
        )

        print("\n==================================================")
        print("    DSP POWER SPECTRAL DENSITY ANALYSIS MATRIX    ")
        print("==================================================")
        print(f"Center Frequency: {freq} MHz")
        print(f"Doppler Bins:    {frequencies.shape[0]} ({frequencies.min():.2f} Hz to {frequencies.max():.2f} Hz)")
        print(f"Time Bins:       {spec_times.shape[0]}")
        print(f"PSD Shape:       {Sxx_db.shape}")
        print(f"Power Bounds:    Min {Sxx_db.min():.2f} dB, Max {Sxx_db.max():.2f} dB")
    else:
        metadata, df = dataset
        print("\n==================================================")
        print("          LEGATE GRAPE CSV DATA LOADED            ")
        print("==================================================")
        print("Metadata:", metadata)
        print("\nData Frame Head:\n", df.head())


if __name__ == "__main__":
    main()