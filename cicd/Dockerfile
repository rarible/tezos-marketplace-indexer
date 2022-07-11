ARG BASE_IMAGE_VERSION=3.9.7-slim-buster
FROM rarible/python:${BASE_IMAGE_VERSION}

COPY requirements.txt /requirements.txt

RUN apt-get update && apt-get install -y libsodium-dev libsecp256k1-dev libgmp-dev pkg-config build-essential
RUN pip install --no-cache-dir -r /requirements.txt && rm -f /requirements.txt

USER nobody:nogroup

WORKDIR /app
COPY . /app

EXPOSE 8080
CMD ["python", "api.py"]