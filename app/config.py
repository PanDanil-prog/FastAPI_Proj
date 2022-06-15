import os

from starlette.config import Config
from starlette.datastructures import Secret


dir_path = os.path.dirname(os.path.realpath(__file__))
config = Config(f'{dir_path[:-3]}.env')

DATABASE_URL = f'postgresql://{config("DATABASE_USER", cast=str)}:' \
               f'{config("DATABASE_PASSWORD", cast=str)}@localhost:5432/{config("DATABASE_NAME", cast=str)}'

MINIO_HOST = config('MINIO_HOST', cast=str)
MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY', cast=str)
MINIO_SECRET_KEY = config('MINIO_SECRET_KEY', cast=str)

SECRET_KEY = config('SECRET_KEY', cast=Secret)
