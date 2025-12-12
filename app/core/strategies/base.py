from abc import ABC, abstractmethod
from typing import Any, List


class BaseStrategy(ABC):
    """
    Abstract Base Class for formatting strategies.
    Defines the contract for processing a pipeline of operations.
    """

    @abstractmethod
    def process(self, value: Any, ops: List[str]) -> Any:
        """
        Process the value through a list of operations.

        Args:
            value (Any): The raw data from Excel.
            ops (List[str]): A list of operation tokens.

        Returns:
            Any: The formatted value.
        """
        pass
