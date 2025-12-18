import json
import logging
from typing import Any, Dict, Optional

import redis

from app.core.config import settings


# Configure Logging
logger = logging.getLogger(__name__)

# Redis Connection
try:
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True,  # Automatically decodes bytes to strings
    )
    redis_client = redis.Redis(connection_pool=pool)
    # Test connection immediately
    redis_client.ping()
    logger.info("[REDIS] Connected successfully.")
except Exception as e:
    logger.error(f"[REDIS] Failed to connect: {e}")
    # Fallback could be implemented here, but we want to fail fast
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
