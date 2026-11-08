import logging
from pathlib import Path
import pandas as pd
import plotly.express as px

logger = logging.getLogger("hamsci_psws.plotting.gantt")


def plot_inventory_gantt(inventory_df: pd.DataFrame, output_html: Path = Path("inventory_gantt.html")):
    """Generates an interactive HTML Gantt chart of data availability across stations."""
    if inventory_df.empty:
        logger.warning("Empty DataFrame passed to plot_inventory_gantt. Skipping chart creation.")
        return None

    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    fig = px.timeline(
        inventory_df,
        x_start="start_time",
        x_end="end_time",
        y="station_id",
        color="instrument_type" if "instrument_type" in inventory_df.columns else None,
        hover_data=[c for c in ["frequency", "data_type"] if c in inventory_df.columns],
        title="PSWS Observation Inventory",
    )
    fig.update_yaxes(autorange="reversed")

    fig.write_html(str(output_html), include_plotlyjs="cdn")

    if output_html.exists() and output_html.stat().st_size > 0:
        logger.info(f"Successfully saved Gantt HTML plot ({output_html.stat().st_size} bytes) -> {output_html.resolve()}")
        print(f"\nSaved interactive Gantt chart: {output_html.resolve()} ({output_html.stat().st_size} bytes)")
    else:
        logger.error(f"Failed to write HTML output file to {output_html}")

    return fig