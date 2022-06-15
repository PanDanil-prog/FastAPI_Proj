from sqlalchemy import create_engine

from app.config import DATABASE_URL
from app.models import Base


def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    main()

