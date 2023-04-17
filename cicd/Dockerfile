ARG BASE_IMAGE_VERSION=3.10-slim-buster
FROM rarible/python:${BASE_IMAGE_VERSION}

COPY requirements.txt /requirements.txt

# dipdup dep requires this
# https://github.com/baking-bad/pytezos#ubuntu-debian-and-other-apt-based-distributions
# https://pypi.org/project/fastecdsa/#installing
RUN apt-get update -y \
    && apt-get install -y git libsodium-dev libsecp256k1-dev libgmp-dev pkg-config build-essential \
    && pip install --no-cache-dir -r /requirements.txt && rm -f /requirements.txt \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache/* \
    && rm -rf /var/lib/apt/lists/*

USER nobody:nogroup
ENV HOME /tmp

WORKDIR /app
COPY . /app

EXPOSE 8080
CMD ["python", "api.py"]
