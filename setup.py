from setuptools import setup

setup(
    name='app-example',
    version='0.0.1',
    author='Danila P',
    author_email='panagushindmwork@gmail.com',
    description='FastAPI-app',
    install_requires=[
        'fastapi==0.78.0',
        'uvicorn==0.17.6',
        'minio==7.1.8',
        'SQLAlchemy==1.4.37',
        'pytest==7.1.2',
        'requests==2.27.1',
        'psycopg2-binary==2.9.3',
        'pydantic==1.9.1',
        'python-multipart==0.0.5',
        'starlette==0.19.1'
    ],
    scripts=['app/main.py', 'scripts/create_db.py']
)
