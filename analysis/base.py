from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any


class BaseAnalysis(ABC):
    """Abstract base class for all analyses."""

    @abstractmethod
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        pass