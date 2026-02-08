import redis
from fastapi import Depends

from app.core.config import settings
from app.core.service import BatchService
from app.integration.state import RedisJobRepository


# Redis Client
def get_redis_client() -> redis.Redis:
    """Dependency provider for Redis client.

    Returns:
        redis.Redis: The configured Redis client.
    """
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True,
    )
    return redis.Redis(connection_pool=pool)


# Initialize global client for use where dependency injection is not available
# (e.g. startup checks) or for caching the connection pool
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
)
global_redis_client = redis.Redis(connection_pool=redis_pool)


def get_job_repository() -> RedisJobRepository:
    """Dependency provider for JobRepository.

    Returns:
        RedisJobRepository: The configured repository instance.
    """
    return RedisJobRepository(global_redis_client)


def get_batch_service(
    repo: RedisJobRepository = Depends(get_job_repository),
) -> BatchService:
    """Dependency provider for BatchService.

    Args:
        repo (RedisJobRepository): Injected repository.

    Returns:
        BatchService: The configured service instance.
    """
    return BatchService(repo)
