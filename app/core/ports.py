from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class JobRepositoryPort(ABC):
    """Port interface for Job Persistence.

    Defines the contract for saving and retrieving job states, adhering to
    Hexagonal Architecture.
    """

    @abstractmethod
    def save(self, job_id: str, data: Dict[str, Any]) -> None:
        """Saves or updates job data.

        Args:
            job_id (str): The unique job identifier.
            data (Dict[str, Any]): The job data to persist.
        """
        pass

    @abstractmethod
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves job data.

        Args:
            job_id (str): The unique job identifier.

        Returns:
            Optional[Dict[str, Any]]: The job data, or None if not found.
        """
        pass

    @abstractmethod
    def update_status(self, job_id: str, status: str, **kwargs) -> None:
        """Updates the status and optional metadata of a job.

        Args:
            job_id (str): The unique job identifier.
            status (str): The new status string.
            **kwargs: Additional fields to update.
        """
        pass

    @abstractmethod
    def add_to_history(self, job_id: str) -> None:
        """Adds a job to the global history list.

        Args:
            job_id (str): The unique job identifier.
        """
        pass

    @abstractmethod
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves a list of recent jobs.

        Args:
            limit (int): The maximum number of jobs to return. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: A list of job dictionaries.
        """
        pass
