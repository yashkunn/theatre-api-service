# Theatre API


API service for theatre management written on DRF

## Installation
### Installing using GitHub

Install PostgresSQL and create db


```bash
git clone https://github.com/yashkunn/theatre-api-service.git

python -m venv venv

source venv/bin/activate

pip install -r requirements. txt

set DB_HOST=<your db hostname>

set DB_NAME=<your db name>

set DB_USER=<your db username>

set DB_PASSWORD=<your db user password>
set SECRET_KEY=<your secret key>

python manage.py migrate

python manage.py runserver
```

## Run with docker
Docker should be installed

```bash
docker-compose build

docker-compose up
```
## Getting access

- Create user  - ```/api/user/register/```
- Get access tocken - ```/api/user/token/```

## Features

- JWT authenticated

- Admin panel /admin/

- Documentation is located at /api/doc/swagger/

- Managing reservations and tickets

- Creating plays with genres, actors

- Creating theatre halls

- Adding performance

- Filtering plays and performance
