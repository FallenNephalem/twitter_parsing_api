import asyncio
import logging
from contextlib import contextmanager
from itertools import chain
from typing import List

import aiohttp

from models import AccountStats, db_session, Status, Twit
from redis import redis_connection
from settings import get_settings

logger = logging.getLogger('twitter-api')


async def parse_twitter_accounts(links: List[str], session_id: str) -> None:
    def get_twitter_username(link):
        if link.endswith('/'):
            return link.split('/')[-2]
        else:
            return link.split('/')[-1]

    usernames = [get_twitter_username(link) for link in links]

    step = get_settings().TWITTER_LIMIT_PER_BATCH_REQUEST

    for username in usernames:
        await redis_connection().set(f'{session_id}:{username}', Status.PENDING.value, ex=60 * 60 * 24)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(0, len(usernames), step):
            tasks.append(parse_twitter_account_batch(session_id, session, usernames[i:i + step]))

        objects = await asyncio.gather(*tasks, return_exceptions=False)
    with contextmanager(db_session)() as session:
        for obj in chain.from_iterable(objects):
            obj.create_or_update(session)
            await redis_connection().set(f'{session_id}:{obj.username}', Status.SUCCESS.value, ex=60 * 60 * 24)


async def parse_twitter_account_batch(
        session_id: str, session: aiohttp.ClientSession, usernames: List[str]) -> List[AccountStats]:

    res = []
    headers = {'Authorization': f'bearer {get_settings().AUTH_TOKEN}'}
    params = {'usernames': ','.join(usernames), 'user.fields': 'public_metrics,description'}
    endpoint = f'{get_settings().TWITTER_ENDPOINT}/by'
    try:
        async with session.get(endpoint, headers=headers, params=params) as response:
            logging.info(msg={
                'endpoint': endpoint,
                'params': params,
                'status': response.status
            })
            for account_data in (await response.json())['data']:
                res.append(AccountStats.from_twitter_api(account_data))
        return res
    except Exception as e:
        logging.exception(e, exc_info=True)
        for username in usernames:
            await redis_connection().set(f'{session_id}:{username}', Status.PENDING.value, ex=60 * 60 * 24)
        return []


async def get_twits(twitter_id: str):
    endpoint = f'{get_settings().TWITTER_ENDPOINT}/{twitter_id}/tweets'
    headers = {'Authorization': f'bearer {get_settings().AUTH_TOKEN}'}
    params = {'tweet.fields': 'created_at'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, params=params) as response:
                logging.info(msg={
                    'twitter_id': twitter_id,
                    'endpoint': endpoint,
                    'params': params,
                    'status': response.status
                })
                res = [Twit(text=twit['text'], created_at=twit['created_at']) for twit in (await response.json())['data']]
        return res
    except Exception as e:
        logging.exception(e, exc_info=True)
        return []
