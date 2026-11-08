import numpy as np
from scipy import signal

def compute_doppler_psd(iq_data: np.ndarray, sample_rate: float, nfft: int = 1024, window: str = "hann"):
    """
    Computes shifted 2D Power Spectral Density (PSD) matrix and frequency array from IQ samples.
    """
    f, t_spec, Sxx = signal.spectrogram(
        iq_data, fs=sample_rate, nfft=nfft, window=window, return_onesided=False
    )
    
    # Shift zero frequency to centre
    f_shifted = np.fft.fftshift(f).astype("float64")
    Sxx_shifted = np.fft.fftshift(Sxx, axes=0)
    Sxx_db = 10 * np.log10(Sxx_shifted)
    
    return f_shifted, t_spec, Sxx_db
