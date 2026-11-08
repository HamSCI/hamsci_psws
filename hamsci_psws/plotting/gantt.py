from pathlib import Path
import pandas as pd
import plotly.express as px

def plot_inventory_gantt(inventory_df: pd.DataFrame, output_html: Path = Path("inventory_gantt.html")):
    """Generates an interactive HTML Gantt chart of data availability across stations."""
    fig = px.timeline(
        inventory_df, 
        x_start="start_time", 
        x_end="end_time", 
        y="station_id", 
        color="instrument_type", 
        hover_data=["frequency", "data_type"], 
        title="PSWS Observation Inventory"
    )
    fig.update_yaxes(autorange="reversed")
    fig.write_html(str(output_html))
    return fig