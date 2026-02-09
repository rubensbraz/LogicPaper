import asyncio
import os
import shutil
import subprocess
import zipfile
from typing import Any, Dict, List, Optional

from app.core.ports import ProcessPort, StoragePort


class FileSystemAdapter(StoragePort):
    """Adapter for local file system operations."""

    def list_dir(self, dir_path: str) -> List[str]:
        """Lists all files and directories in a directory (filenames only)."""
        if not os.path.exists(dir_path):
            return []
        return os.listdir(dir_path)

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
        if not os.path.exists(dir_path):
            return []

        files = []
        if recursive:
            for root, _, filenames in os.walk(dir_path):
                for f in filenames:
                    if extension and not f.lower().endswith(extension.lower()):
                        continue
                    files.append(os.path.join(root, f))
        else:
            for f in os.listdir(dir_path):
                if extension and not f.lower().endswith(extension.lower()):
                    continue
                files.append(os.path.join(dir_path, f))
        return files

    def exists(self, path: str) -> bool:
        """Checks if a file or directory exists."""
        return os.path.exists(path)

    def copy(self, src: str, dst: str) -> None:
        """Copies a file or directory."""
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    def make_dir(self, path: str) -> None:
        """Creates a directory if it does not exist."""
        os.makedirs(path, exist_ok=True)

    def delete(self, path: str) -> None:
        """Deletes a file or directory recursively."""
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def extract_zip(self, zip_path: str, extract_to: str) -> None:
        """Extracts a ZIP archive."""
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

    def create_zip(self, source_dir: str, output_path: str) -> None:
        """Creates a ZIP archive from a directory."""
        shutil.make_archive(output_path, "zip", source_dir)

    def read_text(self, path: str) -> str:
        """Reads text from a file."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, path: str, content: str) -> None:
        """Writes text to a file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def read_binary(self, path: str) -> bytes:
        """Reads binary data from a file."""
        with open(path, "rb") as f:
            return f.read()

    def write_binary(self, path: str, content: bytes) -> None:
        """Writes binary data to a file."""
        with open(path, "wb") as f:
            f.write(content)

    def basename(self, path: str) -> str:
        """Returns the base name of pathname path."""
        return os.path.basename(path)

    def splitext(self, path: str) -> tuple[str, str]:
        """Splits the path into a pair (root, ext)."""
        return os.path.splitext(path)

    def dirname(self, path: str) -> str:
        """Returns the directory name of pathname path."""
        return os.path.dirname(path)

    def join_path(self, *paths: str) -> str:
        """Joins path components intelligently."""
        return os.path.join(*paths)

    def is_safe_path(self, base_path: str, target_path: str) -> bool:
        """Checks if the target path is safely within the base path."""
        try:
            base = os.path.abspath(base_path)
            target = os.path.abspath(target_path)
            # Use os.path.commonpath to be robust across OS
            return os.path.commonpath([base]) == os.path.commonpath([base, target])
        except Exception:
            return False


class LibreOfficeAdapter(ProcessPort):
    """Adapter for executing LibreOffice commands via subprocess."""

    async def run_command(self, cmd: List[str], timeout: int) -> Dict[str, Any]:
        """Executes a subprocess command asynchronously.

        Args:
            cmd (List[str]): The command and arguments.
            timeout (int): Timeout in seconds.

        Returns:
            Dict[str, Any]: Result containing 'returncode', 'stdout', 'stderr'.
        """
        try:
            process = await asyncio.to_thread(
                subprocess.run,
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            return {
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": b"",
                "stderr": b"Timeout Expired",
            }
        except Exception as e:
            return {
                "returncode": 1,
                "stdout": b"",
                "stderr": str(e).encode(),
            }
