import asyncio
import json
import logging
from typing import Any, Dict, Optional

import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError

from app.core.config import settings

# Configure Logging
logger = logging.getLogger(__name__)


async def get_redis_async() -> aioredis.Redis:
    """Creates an async Redis client for Pub/Sub."""
    return aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True,
    )


async def log_generator(session_id: str):
    """Async generator for Server-Sent Events (SSE) using Redis Pub/Sub.

    Args:
        session_id (str): The session ID to stream logs for.

    Yields:
        str: Server-sent event data.
    """
    redis_client = await get_redis_async()
    pubsub = redis_client.pubsub()
    channel_name = f"{settings.REDIS_LOG_CHANNEL_PREFIX}{session_id}"

    try:
        await pubsub.subscribe(channel_name)

        # Generator lifetime loop
        while True:
            try:
                # Get message with timeout to allow for heartbeat
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )

                if message:
                    data = message["data"]
                    yield f"data: {data}\n\n"

                    if "PROCESS_COMPLETE" in data or "PROCESS_ERROR" in data:
                        break
                else:
                    # Prevent tight loop if get_message returns immediately without waiting for timeout
                    await asyncio.sleep(0.5)

            except ConnectionError:
                yield "data: CONNECTION_LOST\n\n"
                break
            except Exception as e:
                logger.error(f"SSE Stream error for session {session_id}: {e}")
                break

    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
        await redis_client.close()
        logger.info(f"SSE Redis Sub closed for session: {session_id}")


def send_log(session_id: str, message: str) -> None:
    """Push a log message to the specific session channel via Redis.

    This uses a synchronous connection since it's called from sync contexts
    or sync wrappers.

    Args:
        session_id (str): The session identifier.
        message (str): The message to send.
    """
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        channel_name = f"{settings.REDIS_LOG_CHANNEL_PREFIX}{session_id}"
        r.publish(channel_name, message)
        r.close()
    except Exception as e:
        logger.error(f"Redis Publish Error: {e}")


def send_log_event(
    session_id: str, code: str, params: Optional[Dict[str, Any]] = None
) -> None:
    """Helper to send a structured JSON log event."""
    payload = {"code": code}
    if params:
        payload["params"] = params
    send_log(session_id, json.dumps(payload))
