from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAPIClient(ABC):
    """Abstract base class for all API clients."""

    @abstractmethod
    def fetch(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from API."""
        pass