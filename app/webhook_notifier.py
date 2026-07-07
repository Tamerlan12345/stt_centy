import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
TIMEOUT_SECONDS = 40
RETRY_BACKOFF_SECONDS = [2, 4]  # delay before attempts 2 and 3


async def send_callback(callback_url: str, payload: dict) -> bool:
    """POSTs the task result JSON to a caller-supplied callback URL.

    Retries on failure with backoff. Never raises - a broken callback
    must not affect task processing or the polling endpoints.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(callback_url, json=payload)
                response.raise_for_status()
                logger.info(f"Callback delivered to {callback_url} (attempt {attempt})")
                return True
            except Exception as e:
                logger.warning(f"Callback attempt {attempt}/{MAX_RETRIES} to {callback_url} failed: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS[attempt - 1])

    logger.error(f"Callback to {callback_url} failed after {MAX_RETRIES} attempts")
    return False
