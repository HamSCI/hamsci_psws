from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy import signal
from astropy.coordinates import EarthLocation, AltAz, get_sun
from astropy.time import Time
import astropy.units as u


def calculate_solar_elevation(times: list, lat: float, lon: float) -> np.ndarray:
    """Calculates solar elevation angles in degrees for a time series and location."""
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    astro_times = Time(times)
    altaz_frame = AltAz(obstime=astro_times, location=location)
    sun_altaz = get_sun(astro_times).transform_to(altaz_frame)
    return sun_altaz.alt.deg


def plot_rx888_spectrogram(
    dataset: xr.Dataset,
    freq_mhz: float,
    nfft: int = 1024,
    cmap: str = "viridis",
    overlay_solar: bool = True,
    output_path: Path = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Generates an RX888 spectrogram with an Astropy solar elevation overlay."""
    iq_signal = dataset.sel(frequency=freq_mhz)["iq"].values
    fs = dataset.attrs["sample_rate"]
    time_utc = dataset["time"].values

    # Calculate spectrogram and shift 0 Hz to center
    f, t_spec, Sxx = signal.spectrogram(
        iq_signal, fs=fs, nfft=nfft, window="hann", return_onesided=False
    )
    f = np.fft.fftshift(f).astype("float64")
    Sxx = np.fft.fftshift(Sxx, axes=0)
    Sxx_db = 10 * np.log10(Sxx)

    fig, ax1 = plt.subplots(figsize=(13, 6))

    # Map t_spec (seconds) to UTC datetimes
    ts0 = Time(time_utc[0]).unix
    ts1 = Time(time_utc[-1]).unix
    spec_times = Time(np.linspace(ts0, ts1, len(t_spec)), format="unix").datetime

    mesh = ax1.pcolormesh(spec_times, f, Sxx_db, cmap=cmap, shading="auto")
    callsign = dataset.attrs.get("callsign", "Station")
    ax1.set_title(f"Doppler Shift Spectrogram - {freq_mhz} MHz ({callsign})")
    ax1.set_xlabel("Time (UTC)")
    ax1.set_ylabel("Doppler Shift (Hz)")

    # 1. Attach colorbar FIRST so ax1 resizes before twinx() is created
    fig.colorbar(mesh, ax=ax1, label="PSD (dB)", pad=0.08)

    # 2. Solar Elevation Overlay on twinx() AFTER ax1 colorbar resize
    if overlay_solar and "latitude" in dataset.attrs and "longitude" in dataset.attrs:
        lat = dataset.attrs["latitude"]
        lon = dataset.attrs["longitude"]

        solar_elev = calculate_solar_elevation(spec_times, lat, lon)

        ax2 = ax1.twinx()
        (line_elev,) = ax2.plot(
            spec_times,
            solar_elev,
            color="white",
            linestyle="--",
            linewidth=1.5,
            alpha=0.9,
            label="Solar Elev (°)",
        )
        ax2.axhline(0, color="yellow", linestyle=":", linewidth=1.0, alpha=0.7)  # Horizon line
        ax2.set_ylabel("Solar Elevation (°)", color="black", fontsize=10)
        ax2.tick_params(axis="y", labelcolor="black", labelsize=9)
        ax2.set_ylim(-90, 90)

        # Inset dark legend box inside top right of plot frame
        ax2.legend(
            handles=[line_elev],
            loc="upper right",
            facecolor="black",
            labelcolor="white",
            framealpha=0.6,
            fontsize=9,
        )

    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")

    return fig, ax1