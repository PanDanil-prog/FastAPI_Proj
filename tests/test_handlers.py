from datetime import datetime
from unittest import TestCase
from uuid import uuid4

from fastapi.testclient import TestClient

from app.utils import get_password_hash
from app.main import app
from app.models import connect_db, User, AuthToken, Inbox, minio_client


class CreateUserTestCase(TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_main_url(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_create_user_valid(self):
        database = connect_db()

        user_exist = database.query(User).filter(User.email == 'test@test.com').one_or_none()
        if user_exist:
            database.query(User).filter(User.email == 'test@test.com').delete()
            database.commit()

        response = self.client.post('/user', json={"user": {
            "email": "test@test.com",
            "password": get_password_hash('123'),
            "first_name": "test",
            "last_name": "test_user",
            "nickname": "test_nick"
        }})

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'User id': user_id})

        database.query(User).filter(User.email == 'test@test.com').delete()
        database.commit()

    def test_create_user_group_admin(self):
        database = connect_db()

        response = self.client.post('/user', json={"user": {
            "email": "admin@test.com",
            "password": get_password_hash('123'),
            "first_name": "test",
            "last_name": "test_user",
            "nickname": "test_nick"
        }})

        user_id = database.query(User).filter(User.email == 'admin@test.com').one_or_none().id

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'User id': user_id})

        database.query(User).filter(User.email == 'admin@test.com').delete()
        database.commit()

    def test_create_user_group_moderator(self):
        database = connect_db()

        response = self.client.post('/user', json={"user": {
            "email": "moder@test.com",
            "password": get_password_hash('123'),
            "first_name": "test",
            "last_name": "test_user",
            "nickname": "test_nick"
        }})

        user_id = database.query(User).filter(User.email == 'moder@test.com').one_or_none().id

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'User id': user_id})

        database.query(User).filter(User.email == 'moder@test.com').delete()
        database.commit()

    def test_create_user_invalid(self):
        database = connect_db()

        new_user = User(
            email='test@test.com',
            group='user',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

        response = self.client.post('/user', json={"user": {
            "email": "test@test.com",
            "password": get_password_hash('123'),
            "first_name": "test",
            "last_name": "test_user",
            "nickname": "test_nick"
        }})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Email already exists'})

        database.query(User).filter(User.email == 'test@test.com').delete()
        database.commit()


class LoginUserTestCase(TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)

        database = connect_db()

        new_user = User(
            email='test@test.com',
            group='user',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

    def tearDown(self) -> None:
        database = connect_db()

        database.query(User).filter(User.email == 'test@test.com').delete()
        database.commit()

    def test_user_login_email_invalid(self):
        response = self.client.post('/login', json={"user_form": {
            "email": "invalidemail@test.com",
            "password": "123"
        }})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {'detail': 'Email/password invalid'})

    def test_user_login_password_invalid(self):
        response = self.client.post('/login', json={"user_form": {
            "email": "test@test.com",
            "password": "124"
        }})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {'detail': 'Email/password invalid'})

    def test_user_login_valid(self):
        database = connect_db()

        response = self.client.post('/login', json={"user_form": {
            "email": "test@test.com",
            "password": '123'
        }})

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id
        auth_token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'Auth Token': auth_token})

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.commit()

    def test_user_login_token_already_exist(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id

        auth_token = AuthToken(
            token=str(uuid4()),
            user_id=user_id
        )

        database.add(auth_token)
        database.commit()

        response = self.client.post('/login', json={"user_form": {
            "email": "test@test.com",
            "password": '123'
        }})

        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'Auth Token': token})

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.commit()


class GetImagesTestCase(TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)
        database = connect_db()

        new_user = User(
            email='test@test.com',
            group='user',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id

        auth_token = AuthToken(token=str(uuid4()), user_id=user_id)
        database.add(auth_token)
        database.commit()

        new_image = Inbox(
            request_code='12345',
            file_name=str(uuid4())
        )

        database.add(new_image)
        database.commit()

    def tearDown(self) -> None:
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.query(User).filter(User.id == user_id).delete()
        database.query(Inbox).filter(Inbox.request_code == '12345').delete()
        database.commit()

    def test_get_images_valid_token_valid_code(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id
        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token
        images = database.query(Inbox).filter(Inbox.request_code == '12345').all()
        code = '12345'

        response = self.client.get(f'/frames/{token}/{code}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(),
                         {code: [{'file_name': image.file_name, 'created_at': image.created_at} for image in images]})

    def test_get_images_invalid_token(self):
        code = '12345'
        response = self.client.get(f'/frames/1/{code}')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'AuthToken dont exist'})

    def test_get_images_valid_token_invalid_code(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id
        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token
        code = '123'

        response = self.client.get(f'/frames/{token}/{code}')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': f'Images with code {code} doesnt exist'})


class DeleteImagesTestCase(TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)
        database = connect_db()

        new_user = User(
            email='admintest@test.com',
            group='admin',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id

        auth_token = AuthToken(token=str(uuid4()), user_id=user_id)
        database.add(auth_token)
        database.commit()

        request_code = str(datetime.utcnow()).replace(':', '').replace('-', '').replace(' ', '').replace('.', '')
        file_name = 'test_image'
        new_image = Inbox(
            request_code=request_code,
            file_name=file_name
        )

        database.add(new_image)
        database.commit()

        bucket_name = request_code[:8]
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        minio_client.fput_object(bucket_name, file_name + '.jpg', 'tests/images_for_test/testimage.jpg')

    def tearDown(self) -> None:
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.query(User).filter(User.id == user_id).delete()

        database.commit()

        image = database.query(Inbox).filter(Inbox.file_name == 'test_image').one_or_none()

        if image:
            database.query(Inbox).filter(Inbox.file_name == 'test_image').delete()
            minio_client.remove_object(image.request_code[:8], 'test_image.jpg')
            database.commit()

    def test_delete_images_valid_data(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id
        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token
        request_code = database.query(Inbox).filter(Inbox.file_name == 'test_image').one_or_none().request_code

        response = self.client.delete(f'/frames/{token}/{request_code}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), f'Images with code {request_code} was deleted')

    def test_delete_images_invalid_token(self):

        token = 'not_valid_token'
        request_code = 'some_valid_code'

        response = self.client.delete(f'/frames/{token}/{request_code}')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'AuthToken dont exist'})

    def test_delete_images_valid_token_invalid_group(self):
        database = connect_db()

        new_user = User(
            email='test@test.com',
            group='user',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id

        auth_token = AuthToken(
            token=str(uuid4()),
            user_id=user_id
        )

        database.add(auth_token)
        database.commit()

        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token
        request_code = database.query(Inbox).filter(Inbox.file_name == 'test_image').one_or_none().request_code

        response = self.client.delete(f'/frames/{token}/{request_code}')

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'detail': 'You must be admin/moderator'})

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.query(User).filter(User.email == 'test@test.com').delete()
        database.commit()

    def test_delete_images_valid_token_valid_group_invalid_code(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id
        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token
        request_code = 'invalid_request_code'

        response = self.client.delete(f'/frames/{token}/{request_code}')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': f'Images with code {request_code} doesnt exist'})


class UploadImagesTestCase(TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)
        database = connect_db()

        new_user = User(
            email='admintest@test.com',
            group='admin',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id

        auth_token = AuthToken(token=str(uuid4()), user_id=user_id)
        database.add(auth_token)
        database.commit()

    def tearDown(self) -> None:
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.query(User).filter(User.id == user_id).delete()

        database.commit()

    def test_upload_images_valid_data(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id
        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token

        with open('tests/images_for_test/testimage.jpg', 'rb') as image:
            response = self.client.post(f'/frames/{token}', files={'files': ('testimage.jpg', image, 'image/jpeg')})
            request_code = str(datetime.utcnow()).replace(':', '').replace('-', '').replace(' ', '').replace('.', '')[
                           :-6]
            bucket_name = request_code[:8]

        images = database.query(Inbox).filter(Inbox.request_code == request_code).all()
        assert_response = {request_code: []}

        for image in images:
            assert_response[request_code].append(
                {'file_name': image.file_name, 'created_at': image.created_at})
            minio_client.remove_object(bucket_name, image.file_name+'.jpg')

        database.query(Inbox).filter(Inbox.request_code == request_code).delete()
        database.commit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), assert_response)

    def test_upload_images_invalid_token(self):
        token = 'some_invalid_token'
        with open('tests/images_for_test/testimage.jpg', 'rb') as image:
            response = self.client.post(f'/frames/{token}', files={'files': ('testimage.jpg', image, 'image/jpeg')})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'AuthToken dont exist'})

    def test_upload_images_valid_token_invalid_group(self):
        database = connect_db()

        new_user = User(
            email='test@test.com',
            group='user',
            password=get_password_hash('123'),
            first_name='test',
            last_name='test',
            nickname='test',
        )

        database.add(new_user)
        database.commit()

        user_id = database.query(User).filter(User.email == 'test@test.com').one_or_none().id

        auth_token = AuthToken(
            token=str(uuid4()),
            user_id=user_id
        )

        database.add(auth_token)
        database.commit()

        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token

        with open('tests/images_for_test/testimage.jpg', 'rb') as image:
            response = self.client.post(f'/frames/{token}', files={'files': ('testimage.jpg', image, 'image/jpeg')})

        database.query(AuthToken).filter(AuthToken.user_id == user_id).delete()
        database.query(User).filter(User.email == 'test@test.com').delete()
        database.commit()

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'detail': 'You must be admin/moderator'})

    def test_upload_images_invalid_format(self):
        database = connect_db()

        user_id = database.query(User).filter(User.email == 'admintest@test.com').one_or_none().id
        token = database.query(AuthToken).filter(AuthToken.user_id == user_id).one_or_none().token

        with open('tests/images_for_test/testimage.jpg', 'rb') as image:
            response = self.client.post(f'/frames/{token}', files={'files': ('testimage', image, 'image/jpeg')})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'All images must be in format .jpg'})
