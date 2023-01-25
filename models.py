from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic.main import BaseModel
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy import orm, create_engine

from settings import get_settings

Base = orm.declarative_base()
engine = create_engine(get_settings().SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = orm.sessionmaker(engine)


def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    Base.metadata.create_all(bind=engine)


class Twit(BaseModel):
    text: str
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.strftime('%a %b %y %H:%M:%S %z %Y')
        }


class Status(Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'


class UserStatus(BaseModel):
    username: str
    status: Status


class AccountStats(Base):
    __tablename__ = 'statistic'
    id = Column(Integer, primary_key=True, index=True)
    twitter_id = Column(String(64), unique=True, index=True)
    name = Column(String(64))
    username = Column(String(64), unique=True, index=True)
    following_count = Column(Integer)
    followers_count = Column(Integer)
    description = Column(Text)

    def create_or_update(self, session: orm.Session) -> AccountStats:
        instance = session.query(self.__class__).filter_by(twitter_id=self.twitter_id).first()
        if instance:
            instance.name = self.name
            instance.username = self.username
            instance.following_count = self.following_count
            instance.followers_count = self.followers_count
            instance.description = self.description
            session.add(instance)
        else:
            session.add(self)
        session.commit()
        return instance

    @classmethod
    def from_twitter_api(cls, data: dict) -> AccountStats:
        return cls(
            twitter_id=data['id'],
            name=data['name'],
            username=data['username'],
            following_count=data['public_metrics']['following_count'],
            followers_count=data['public_metrics']['followers_count'],
            description=data['description'],
        )


class GetAccountStats(BaseModel):
    twitter_id: str
    name: str
    username: str
    following_count: int
    followers_count: int
    description: Optional[str]

    class Config:
        orm_mode = True
