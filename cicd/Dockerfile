ARG BASE_IMAGE_VERSION=3.9.7-slim-buster
FROM rarible/python:${BASE_IMAGE_VERSION}

COPY requirements.txt /requirements.txt

RUN apt-get update -y \
    && apt-get install -y libsodium-dev libsecp256k1-dev libgmp-dev pkg-config build-essential \
    && pip install --no-cache-dir -r /requirements.txt && rm -f /requirements.txt \
    && rm -rf /tmp \
    && rm -rf /root/.cache \
    && rm -rf `find /usr/local/lib $POETRY_PATH/venv/lib $VENV_PATH/lib -name __pycache__` \
    && rm -rf /var/lib/apt/lists/*

USER nobody:nogroup

WORKDIR /app
COPY . /app

EXPOSE 8080
CMD ["python", "api.py"]