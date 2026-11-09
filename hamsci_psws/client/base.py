from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd

class BasePSWSClient(ABC):
    """Abstract base class for PSWS data access clients."""

    @abstractmethod
    def query_inventory(self, start_date: str, end_date: str, **kwargs) -> pd.DataFrame:
        """Query station observation inventory."""
        pass

    @abstractmethod
    def download_dataset(self, inventory_df: pd.DataFrame, target_dir: Path, unpack: bool = True) -> list[Path]:
        """Download dataset files for specified observation records."""
        pass
