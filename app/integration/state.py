import json
import logging
from typing import Any, Dict, List, Optional

import redis

from app.core.config import settings
from app.core.ports import JobRepositoryPort

# Configure Logging
logger = logging.getLogger(__name__)


class RedisJobRepository(JobRepositoryPort):
    """Redis-based implementation of the JobRepositoryPort.

    Persists job state and history using Redis keys and lists.
    """

    def __init__(self, redis_client: redis.Redis):
        """Initializes the repository with a Redis client.

        Args:
            redis_client (redis.Redis): The Redis client instance.
        """
        self.redis_client = redis_client
        self.expiration_seconds = settings.REDIS_JOB_TTL

    def save(self, job_id: str, data: Dict[str, Any]) -> None:
        """Persists job data to Redis with an expiration time.

        Args:
            job_id (str): The unique job identifier.
            data (Dict[str, Any]): The job data dictionary to store.
        """
        try:
            # Serialize Dict to JSON String
            # default=str handles datetime objects automatically
            payload = json.dumps(data, default=str)

            self.redis_client.set(
                name=job_id, value=payload, ex=self.expiration_seconds
            )
        except Exception as e:
            logger.error(f"Redis Save Error ({job_id}): {e}")

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves and deserializes job data from Redis.

        Args:
            job_id (str): The unique job identifier.

        Returns:
            Optional[Dict[str, Any]]: The job data dictionary, or None if not found/error.
        """
        try:
            payload = self.redis_client.get(job_id)
            if payload:
                return json.loads(payload)
            return None
        except Exception as e:
            logger.error(f"Redis Get Error ({job_id}): {e}")
            return None

    def update_status(self, job_id: str, status: str, **kwargs) -> None:
        """Updates the status and optional metadata of a job.

        Fetches the current state, updates the fields, and saves it back.
        Note: This is not atomic, but sufficient for this architecture.

        Args:
            job_id (str): The unique job identifier.
            status (str): The new status string.
            **kwargs: Additional fields to update.
        """
        current_data = self.get(job_id) or {}
        current_data["status"] = status
        current_data.update(kwargs)
        self.save(job_id, current_data)

    def add_to_history(self, job_id: str) -> None:
        """Adds a job to the global history list.

        Args:
            job_id (str): The unique job identifier.
        """
        try:
            # LPUSH adds to the head of the list (newest first)
            self.redis_client.lpush("jobs:history", job_id)
            # Trim list to keep only last 50 jobs
            self.redis_client.ltrim("jobs:history", 0, 49)
        except Exception as e:
            logger.error(f"Redis History Add Error: {e}")

    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves a list of recent jobs with their statuses.

        Args:
            limit (int): The maximum number of jobs to return. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: A list of job dictionaries.
        """
        try:
            # Get job IDs
            job_ids = self.redis_client.lrange("jobs:history", 0, limit - 1)
            results = []

            for jid in job_ids:
                data = self.get(jid)
                if data:
                    # Enrich with ID if missing
                    if "job_id" not in data:
                        data["job_id"] = jid
                    results.append(data)

            return results
        except Exception as e:
            logger.error(f"Redis History List Error: {e}")
            return []
