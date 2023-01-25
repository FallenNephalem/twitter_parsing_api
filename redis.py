from typing import AsyncIterator, List
import aioredis

from models import UserStatus
from settings import get_settings

redis_pool = None


async def init_redis() -> AsyncIterator[aioredis.Redis]:
    global redis_pool
    if redis_pool is None:
        pool = await aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
        redis_pool = pool
    return redis_pool


def redis_connection():
    return redis_pool


async def get_session_status(session_id: str) -> List[UserStatus]:
    res = []
    keys = await redis_connection().keys(f'{session_id}:*')
    values = await redis_connection().mget(keys)
    for k, v in zip(keys, values):
        _, username = k.split(':')
        res.append(UserStatus(username=username, status=v))
    return res
