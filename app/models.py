from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

from minio import Minio

from app.config import DATABASE_URL, MINIO_SECRET_KEY, MINIO_ACCESS_KEY, MINIO_HOST


def connect_db():
    engine = create_engine(DATABASE_URL)
    session = Session(bind=engine)
    return session


minio_client = Minio(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    group = Column(String, default='user')
    email = Column(String)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    nickname = Column(String)
    created_at = Column(String, default=datetime.utcnow())


class AuthToken(Base):
    __tablename__ = 'auth_token'

    id = Column(Integer, primary_key=True)
    token = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(String, default=datetime.utcnow())


class Inbox(Base):
    __tablename__ = 'inbox'

    request_code = Column(String)
    file_name = Column(String, primary_key=True)
    created_at = Column(String, default=str(datetime.utcnow())[:-7])
