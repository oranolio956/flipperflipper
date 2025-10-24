FROM mcr.microsoft.com/devcontainers/python:3.11

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libmagic1 \
    redis-server \
    sqlite3 \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel
