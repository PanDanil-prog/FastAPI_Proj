# FastAPI with connection to PostgreSQL and MinIO

---

## Descriprion

This is one of my first projects. This Web Service allows:

- ### Create User (/user)
  - Email and password necessary
  - User had a group by email (if email starts with admin/moder, user group == admin/moder, else - user)
  - Only admin and moderator can upload and delete images
  - Password is hashed by sha256
  - Return user id in Database
- ### Login User (/login)
  - When user created he can login by email and password
  - After authorization user receives a token by which he can access other methods
  - The token is updated if the user logs in not for the first time, otherwise it is simply created
  - Return Token
- ### Upload images to PostgreSQL and MinIO (/frames/auth_token)
  - Only admin/moderator have access to this method
  - You can upload up to 15 images and in .jpg format
  - Return json with uploaded images names and creation time
- ### Get data about uploaded images (/frames/auth_token/code)
  - Everyone, who have token can get images by code
  - Return json with images names and creation time
- ### Delete images (/frames/auth_token/code)
  - Only admin/moderator have access to this method
  - If successfully return string with code of deleted images


## First of all

- You must have installed MinIO server/client:  <https://docs.min.io/docs/minio-quickstart-guide.html>
- You must have installed PostgreSQL

## How to setup

- Clone repo: git clone <https://github.com/PanDanil-prog/FastAPI_Proj>
- Go to cloned directory: cd FastAPI_proj
- Create .env file: nano .env(Put there database and minio data, also secret key for passwords)
- Install requirements from setup.py: pip install -e .
- Go to /app: cd app
- Run the server: uvicorn main:app

If you are watching this, leave a comment on what you think could be improved and what is overkill.

---

## Thank you for your attention!

Contacts:

- Email: panagushindmwork@gmail.com
- Telegram: @panagushindm
- VK: https://vk.com/napchik
