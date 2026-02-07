import json
import logging
import time
from typing import Any, Dict, Optional

import redis

from app.core.config import settings


# Configure Logging
logger = logging.getLogger(__name__)

# Redis Connection with Retry Logic
for attempt in range(settings.REDIS_MAX_RETRIES):
    try:
        pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        redis_client = redis.Redis(connection_pool=pool)
        redis_client.ping()
        logger.info("[REDIS] Connected successfully.")
        break
    except Exception as e:
        if attempt < settings.REDIS_MAX_RETRIES - 1:
            logger.warning(
                f"[REDIS] Connection failed. Retrying in {settings.REDIS_RETRY_DELAY}s... "
                f"({attempt + 1}/{settings.REDIS_MAX_RETRIES})"
            )
            time.sleep(settings.REDIS_RETRY_DELAY)
        else:
            logger.error(
                f"[REDIS] Failed to connect after {settings.REDIS_MAX_RETRIES} attempts: {e}"
            )

            raise e


class JobRepository:
    """Persistence Layer for Job Status using Redis.

    Replaces in-memory dictionary to ensure data survival across restarts.
    """

    # Fetch TTL from centralized settings
    EXPIRATION_SECONDS = settings.REDIS_JOB_TTL

    @staticmethod
    def save(job_id: str, data: Dict[str, Any]) -> None:
        """Saves or updates job data in Redis.

        Args:
            job_id (str): The job identifier.
            data (Dict[str, Any]): The job data to save.
        """
        try:
            # Serialize Dict to JSON String
            # default=str handles datetime objects automatically
            payload = json.dumps(data, default=str)

            redis_client.set(
                name=job_id, value=payload, ex=JobRepository.EXPIRATION_SECONDS
            )
        except Exception as e:
            logger.error(f"Redis Save Error ({job_id}): {e}")

    @staticmethod
    def get(job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves job data from Redis.

        Args:
            job_id (str): The job identifier.

        Returns:
            Optional[Dict[str, Any]]: The job data or None if not found.
        """
        try:
            payload = redis_client.get(job_id)
            if payload:
                return json.loads(payload)
            return None
        except Exception as e:
            logger.error(f"Redis Get Error ({job_id}): {e}")
            return None

    @staticmethod
    def update_status(job_id: str, status: str, **kwargs) -> None:
        """Helper to fetch, update a specific field, and save back.

        Note: This is not atomic, but sufficient for this architecture.

        Args:
            job_id (str): The job identifier.
            status (str): The new status.
            **kwargs: Additional key-value pairs to update.
        """
        current_data = JobRepository.get(job_id) or {}
        current_data["status"] = status
        current_data.update(kwargs)
        JobRepository.save(job_id, current_data)
