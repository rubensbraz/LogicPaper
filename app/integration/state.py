import json
import logging
import time
from typing import Any, Dict, Optional

import redis

from app.core.config import settings


# Configure Logging
logger = logging.getLogger(__name__)

# Redis Connection with Retry Logic

MAX_RETRIES = 5
RETRY_DELAY = 2

for attempt in range(MAX_RETRIES):
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
        if attempt < MAX_RETRIES - 1:
            logger.warning(
                f"[REDIS] Connection failed. Retrying in {RETRY_DELAY}s... ({attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(RETRY_DELAY)
        else:
            logger.error(f"[REDIS] Failed to connect after {MAX_RETRIES} attempts: {e}")

            raise e


class JobRepository:
    """
    Persistence Layer for Job Status using Redis.
    Replaces in-memory dictionary to ensure data survival across restarts.
    """

    # Fetch TTL from centralized settings
    EXPIRATION_SECONDS = settings.REDIS_JOB_TTL

    @staticmethod
    def save(job_id: str, data: Dict[str, Any]) -> None:
        """
        Saves or updates job data in Redis.
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
        """
        Retrieves job data from Redis.
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
        """
        Helper to fetch, update a specific field, and save back.
        Note: This is not atomic, but sufficient for this architecture.
        """
        current_data = JobRepository.get(job_id) or {}
        current_data["status"] = status
        current_data.update(kwargs)
        JobRepository.save(job_id, current_data)
