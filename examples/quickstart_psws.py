import logging
from pathlib import Path
import matplotlib.pyplot as plt

from hamsci_psws import (
    query_inventory,
    plot_inventory_gantt,
    download_dataset,
    read_observation,
    plot_rx888_spectrogram,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main():
    data_dir = Path("./data")
    output_dir = Path("./psws_output")
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    print("--- Step 1: Querying Inventory ---")
    inventory_df = query_inventory(
        start_date="2026-11-05",
        end_date="2026-11-06",
        station_id="S000028",
        frequency=10.0,
    )
    print(inventory_df)

    if inventory_df.empty:
        print("No observations returned from server for selected dates.")
        return

    print("--- Step 2: Plotting Gantt Chart ---")
    gantt_html = output_dir / "inventory_gantt.html"
    plot_inventory_gantt(inventory_df, output_html=gantt_html)
    assert gantt_html.exists(), f"Failed to save Gantt chart at {gantt_html}"
    print(f"Verified Gantt chart saved: {gantt_html.resolve()} ({gantt_html.stat().st_size} bytes)")

    print("--- Step 3: Downloading Observation Dataset into ./data ---")
    download_paths = download_dataset(inventory_df, target_dir=data_dir, unpack=True)
    target_obs = download_paths[0]
    assert target_obs.exists(), f"Downloaded file/directory does not exist: {target_obs}"
    print(f"Verified downloaded observation at: {target_obs.resolve()}")

    print("--- Step 4: Loading Observation Data ---")
    dataset = read_observation(target_obs)
    print(dataset)

    print("--- Step 5: Plotting RX888 Spectrogram ---")
    spec_png = output_dir / "spectrogram_S000028.png"
    fig, ax = plot_rx888_spectrogram(
        dataset=dataset,
        freq_mhz=10.0,
        nfft=1024,
        cmap="viridis",
        overlay_solar=True,
        output_path=spec_png,
    )
    assert spec_png.exists(), f"Failed to save spectrogram image at {spec_png}"
    print(f"Verified spectrogram PNG saved: {spec_png.resolve()} ({spec_png.stat().st_size} bytes)")

    plt.show()


if __name__ == "__main__":
    main()