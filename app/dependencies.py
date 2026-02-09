import redis
from fastapi import Depends

from app.core.config import settings
from app.core.ports import ProcessPort, StoragePort
from app.core.service import BatchService
from app.integration.infrastructure import FileSystemAdapter, LibreOfficeAdapter
from app.integration.state import RedisJobRepository


def get_redis_client() -> redis.Redis:
    """Creates a new Redis client instance.

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


def get_storage_port() -> StoragePort:
    """Dependency provider for StoragePort (FileSystem).

    Returns:
        StoragePort: The configured storage adapter.
    """
    return FileSystemAdapter()


def get_process_port() -> ProcessPort:
    """Dependency provider for ProcessPort (LibreOffice).

    Returns:
        ProcessPort: The configured process adapter.
    """
    return LibreOfficeAdapter()


def get_batch_service(
    repo: RedisJobRepository = Depends(get_job_repository),
    storage: StoragePort = Depends(get_storage_port),
    process: ProcessPort = Depends(get_process_port),
) -> BatchService:
    """Dependency provider for BatchService.

    Args:
        repo (RedisJobRepository): Injected repository.
        storage (StoragePort): Injected storage port.
        process (ProcessPort): Injected process port.

    Returns:
        BatchService: The configured service instance.
    """
    return BatchService(repo, storage, process)
