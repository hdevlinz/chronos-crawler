FROM python:3.12.9-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
   PIP_NO_CACHE_DIR=off \
   PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y curl gnupg apt-transport-https

# Install Brave browser (Release channel)
RUN curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg \
   && echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list \
   && apt-get update \
   && apt-get install -y brave-browser

WORKDIR /app

COPY ./README.md ./
COPY ./pyproject.toml ./
COPY ./poetry.lock ./
COPY ./manage.py ./
COPY ./Makefile ./
COPY chronos ./chronos

RUN pip install poetry && poetry config virtualenvs.create false

RUN poetry install
