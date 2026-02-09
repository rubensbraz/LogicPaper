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
            limit (int, optional): The maximum number of jobs to return. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: A list of job dictionaries containing status and metadata.
        """
        pass


class StoragePort(ABC):
    """Port interface for File System operations.

    Decouples the Domain Layer from direct 'os' and 'shutil' usage.
    """

    @abstractmethod
    def list_dir(self, dir_path: str) -> List[str]:
        """Lists all files and directories in a directory (filenames only).

        Args:
            dir_path (str): The absolute path to the directory.

        Returns:
            List[str]: A list of filenames/directory names.
        """
        pass

    @abstractmethod
    def list_files(
        self, dir_path: str, extension: Optional[str] = None, recursive: bool = False
    ) -> List[str]:
        """Lists files in a directory, optionally filtered by extension.

        Args:
            dir_path (str): The absolute path to the directory.
            extension (Optional[str]): Filter by file extension (e.g., '.docx').
            recursive (bool): Whether to search recursively. Defaults to False.

        Returns:
            List[str]: A list of absolute file paths.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if a file or directory exists.

        Args:
            path (str): The path to check.

        Returns:
            bool: True if it exists, False otherwise.
        """
        pass

    @abstractmethod
    def copy(self, src: str, dst: str) -> None:
        """Copies a file or directory.

        Args:
            src (str): Source path.
            dst (str): Destination path.
        """
        pass

    @abstractmethod
    def make_dir(self, path: str) -> None:
        """Creates a directory if it does not exist.

        Args:
            path (str): The directory path.
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        """Deletes a file or directory recursively.

        Args:
            path (str): The path to delete.
        """
        pass

    @abstractmethod
    def extract_zip(self, zip_path: str, extract_to: str) -> None:
        """Extracts a ZIP archive.

        Args:
            zip_path (str): Path to zip file.
            extract_to (str): Destination directory.
        """
        pass

    @abstractmethod
    def create_zip(self, source_dir: str, output_path: str) -> None:
        """Creates a ZIP archive from a directory.

        Args:
            source_dir (str): The directory to zip.
            output_path (str): The output zip file path (without .zip extension).
        """
        pass

    @abstractmethod
    def read_text(self, path: str) -> str:
        """Reads text from a file.

        Args:
            path (str): File path.

        Returns:
            str: File content.
        """
        pass

    @abstractmethod
    def write_text(self, path: str, content: str) -> None:
        """Writes text to a file.

        Args:
            path (str): File path.
            content (str): Content to write.
        """
        pass

    @abstractmethod
    def read_binary(self, path: str) -> bytes:
        """Reads binary data from a file.

        Args:
            path (str): File path.

        Returns:
            bytes: File content.
        """
        pass

    @abstractmethod
    def join_path(self, *paths: str) -> str:
        """Joins path components intelligently.

        Args:
            *paths (str): Path components.

        Returns:
            str: The joined path.
        """
        pass

    @abstractmethod
    def basename(self, path: str) -> str:
        """Returns the base name of pathname path.

        Args:
            path (str): The file path.

        Returns:
            str: The base name.
        """
        pass

    @abstractmethod
    def splitext(self, path: str) -> tuple[str, str]:
        """Splits the path into a pair (root, ext).

        Args:
            path (str): The file path.

        Returns:
            tuple[str, str]: (root, ext)
        """
        pass

    @abstractmethod
    def dirname(self, path: str) -> str:
        """Returns the directory name of pathname path.

        Args:
            path (str): The file path.

        Returns:
            str: The directory name.
        """
        pass

    @abstractmethod
    def is_safe_path(self, base_path: str, target_path: str) -> bool:
        """Checks if the target path is safely within the base path.

        Prevents directory traversal attacks.

        Args:
            base_path (str): The trusted base directory.
            target_path (str): The path to validate.

        Returns:
            bool: True if safe, False otherwise.
        """
        pass

    @abstractmethod
    def write_binary(self, path: str, content: bytes) -> None:
        """Writes binary data to a file.

        Args:
            path (str): File path.
            content (bytes): Content to write.
        """
        pass


class ProcessPort(ABC):
    """Port interface for executing external processes.

    Decouples the Domain Layer from 'subprocess' calls (e.g., LibreOffice).
    """

    @abstractmethod
    async def run_command(self, cmd: List[str], timeout: int) -> Dict[str, Any]:
        """Executes a subprocess command asynchronously.

        Args:
            cmd (List[str]): The command and arguments.
            timeout (int): Timeout in seconds.

        Returns:
            Dict[str, Any]: Result containing 'returncode', 'stdout', 'stderr'.
        """
        pass
