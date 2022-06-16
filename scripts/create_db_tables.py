from sqlalchemy import create_engine

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.config import DATABASE_URL
from app.models import Base
from app.config import config


def main():
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
    except Exception:
        connection = psycopg2.connect(user='postgres', password='12345', host='localhost')
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = connection.cursor()
        cursor.execute(f'create database {config("DATABASE_NAME", cast=str)}')

        cursor.close()
        connection.close()
    finally:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)


if __name__ == '__main__':
    main()
