import uuid
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File
from starlette import status

from app.forms import UserLoginForm, UserCreateForm
from app.models import connect_db, minio_client, User, AuthToken, Inbox
from app.utils import get_password_hash

router = APIRouter()


@router.get('/')
def read_root():
    return {'message': 'Welcome on home page!'}


@router.post('/user', name='Create User')
def create_user(user: UserCreateForm = Body(..., embed=True), database=Depends(connect_db)):

    # Check if user exist
    exists_user = database.query(User.id).filter(User.email == user.email).one_or_none()

    # If user exist raise exception
    if exists_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already exists')

    # Assign group to user
    if user.email.startswith('admin'):
        group = 'admin'
    elif user.email.startswith('moder'):
        group = 'moderator'
    else:
        group = 'user'

    # Create new user
    new_user = User(
        email=user.email,
        group=group,
        password=get_password_hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        nickname=user.nickname,
    )

    # Commit new user in db
    database.add(new_user)
    database.commit()

    # Return user id
    return {'User id': new_user.id}


@router.post('/login', name='Login User')
def user_login(user_form: UserLoginForm = Body(..., embed=True), database=Depends(connect_db)):

    # Get user from db
    user = database.query(User).filter(User.email == user_form.email).one_or_none()

    # If input data incorrect raise exception
    if not user or get_password_hash(user_form.password) != user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email/password invalid')

    # Check if token for user exist
    if not database.query(AuthToken).filter(AuthToken.user_id == user.id).one_or_none():

        # If token not exist, create new token
        auth_token = AuthToken(token=str(uuid.uuid4()), user_id=user.id)
        database.add(auth_token)

        database.commit()
    else:

        # If token already exist, update it
        auth_token = database.query(AuthToken).filter(AuthToken.user_id == user.id).one_or_none()
        database.query(AuthToken).filter(AuthToken.user_id == user.id).update({AuthToken.token: str(uuid.uuid4()),
                                                                               AuthToken.created_at: datetime.utcnow()})
        database.commit()

    # Return token to user
    return {'Auth Token': auth_token.token}


@router.post('/frames/{auth_token}', name='Upload images')
async def upload_images(auth_token: str, files: list[UploadFile] = File(...), database=Depends(connect_db)):

    # Get user token from db
    auth_token_column = database.query(AuthToken).filter(AuthToken.token == auth_token).one_or_none()

    # Checking if the token exist
    if auth_token_column is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='AuthToken dont exist')
    else:
        # If token exist check user group
        user_column = database.query(User).filter(User.id == auth_token_column.user_id).one_or_none()

        # If user group not admin/moderator raise exception
        if user_column.group not in ['admin', 'moderator']:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail='You must be admin/moderator')

    # Check count of files
    if len(files) > 15 or len(files) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Count of images must be 1-15')

    # Check format of files
    if not all([True if file.filename.endswith('.jpg') else False for file in files]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='All images must be in format .jpg')

    # Preparing important values
    request_code = str(datetime.utcnow()).replace(':', '').replace('-', '').replace(' ', '').replace('.', '')[:-6]
    date = str(datetime.utcnow())[:-7]
    bucket_name = str(datetime.utcnow())[:10].replace('-', '')
    response = {request_code: []}

    # Check bucket exist
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    # Upload images to DB and MinIO
    for file in files:
        # Create file_name
        file_name = str(uuid.uuid4())

        # Create data for db
        new_image = Inbox(
            request_code=request_code,
            file_name=file_name,
            created_at=date
        )

        # Upload images to MinIO
        minio_client.put_object(bucket_name=bucket_name, object_name=file_name + '.jpg',
                                data=BytesIO(bytes(await file.read())),
                                length=-1,
                                part_size=10 * 1024 * 1024
                                )

        # Preparing data to db
        database.add(new_image)

        # Preparing response for user
        response[request_code].append({'file_name': file_name, 'created_at': date})

    database.commit()

    # Return data about created images
    return response


@router.get('/frames/{auth_token}/{code}', name='Get images by request code')
def get_images(auth_token: str, code: str, database=Depends(connect_db)):

    # Get user token from db
    auth_token_column = database.query(AuthToken).filter(AuthToken.token == auth_token).one_or_none()

    # Checking if the token exist
    if auth_token_column is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='AuthToken dont exist')

    # Get images from db
    images = database.query(Inbox).filter(Inbox.request_code == code).all()

    # Checking if the request code exist
    if not images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Images with code {code} doesnt exist')

    # Return the images corresponding to the code
    return {code: [{'file_name': image.file_name, 'created_at': image.created_at} for image in images]}


@router.delete('/frames/{auth_token}/{code}', name='Delete images from DB and MinIO')
def delete_images(auth_token: str, code: str, database=Depends(connect_db)):

    # Get user token from db
    auth_token_column = database.query(AuthToken).filter(AuthToken.token == auth_token).one_or_none()

    # Checking if the token exist
    if auth_token_column is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='AuthToken dont exist')
    else:
        # If token exist check user group
        user_column = database.query(User).filter(User.id == auth_token_column.user_id).one_or_none()

        # If user group not admin/moderator raise exception
        if user_column.group not in ['admin', 'moderator']:
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail='You must be admin/moderator')

    # Get images from db
    images = database.query(Inbox).filter(Inbox.request_code == code).all()

    # Checking if the request code exist
    if not images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Images with code {code} doesnt exist')

    # Create bucket name from date when images was created
    bucket_name = images[0].request_code[:8]

    # Remove images from MinIO
    for image in images:
        minio_client.remove_object(bucket_name, image.file_name + '.jpg')

    # Remove data about images from db
    database.query(Inbox).filter(Inbox.request_code == code).delete()
    database.commit()

    # Return code of deleted images if successfully
    return f'Images with code {code} was deleted'
