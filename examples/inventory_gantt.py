"""
Multi-Station PSWS Data Availability Gantt Chart (2024-2026)
------------------------------------------------------------
Queries observation inventory across multiple stations over a multi-year 
period (2024-2026) and renders an interactive multi-station Gantt timeline.
"""

import logging
from pathlib import Path
import pandas as pd

from hamsci_psws import query_inventory, plot_inventory_gantt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("multi_station_gantt")


def main():
    output_dir = Path("./psws_output")
    output_dir.mkdir(exist_ok=True)
    gantt_path = output_dir / "inventory_gantt_2024_2026.html"

    start_date = "2024-01-01"
    end_date = "2026-12-31"
    stations = ["S000028", "S000049", "S000083", "S000108"]

    logger.info(f"Querying PSWS inventory for stations {stations} from {start_date} to {end_date}...")

    station_dfs = []
    for st_id in stations:
        print(f"\n---> Querying Station: {st_id}")
        try:
            df_st = query_inventory(
                start_date=start_date,
                end_date=end_date,
                station_id=st_id,
            )
            if not df_st.empty:
                logger.info(f"Station {st_id}: Found {len(df_st)} observation records.")
                station_dfs.append(df_st)
            else:
                logger.warning(f"Station {st_id}: No records returned.")
        except Exception as e:
            logger.error(f"Error querying station {st_id}: {e}")

    if not station_dfs:
        logger.warning("No observation records found for any of the requested stations.")
        return

    combined_df = pd.concat(station_dfs, ignore_index=True)

    print("\n==================================================")
    print("      MULTI-STATION INVENTORY SUMMARY (2024-2026)  ")
    print("==================================================")
    print(f"Total Combined Observation Records: {len(combined_df)}")
    print("\nRecords per Station:")
    print(combined_df["station_id"].value_counts().to_string())

    if "instrument_type" in combined_df.columns:
        print("\nRecords by Instrument Type:")
        print(combined_df["instrument_type"].value_counts().to_string())

    # Generate Interactive Multi-Station Gantt Chart
    print("\nGenerating interactive Plotly Gantt chart...")
    fig = plot_inventory_gantt(combined_df, output_html=gantt_path)


if __name__ == "__main__":
    main()