import hashlib
import logging
from datetime import datetime
from typing import List

from fastapi import FastAPI, APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from models import db_session, AccountStats, GetAccountStats, init_db, UserStatus, Twit
from redis import get_session_status, init_redis
from twitter import parse_twitter_accounts, get_twits

logger = logging.getLogger('twitter-api')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_router = APIRouter(
    prefix="/api",
)

app = FastAPI()
app.include_router(api_router)


@app.on_event('startup')
async def startup_event():
    await init_redis()
    init_db()


@app.post("/users/parse")
async def init_account_stats_parsing(links: List[str], background_tasks: BackgroundTasks) -> str:
    session_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()
    background_tasks.add_task(parse_twitter_accounts, links, session_id)
    return session_id


@app.get('/users/status/{session_id}')
async def session_status(session_id: str) -> List[UserStatus]:
    return await get_session_status(session_id)


@app.get("/user/{username}")
async def get_account_stats(username: str, db: Session = Depends(db_session)) -> GetAccountStats:
    instance = db.query(AccountStats).filter_by(username=username).first()
    return GetAccountStats.from_orm(instance)


@app.post("/tweets/{twitter_id}")
async def get_account_twits(twitter_id: str) -> List[Twit]:
    return await get_twits(twitter_id)
