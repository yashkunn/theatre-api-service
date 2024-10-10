FROM python:3.12.0

#set working directory
WORKDIR /usr/src/app

#
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off
ENV PYTHONPATH /


RUN apt update && apt install -y gcc libpq-dev netcat-openbsd coreutils

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
