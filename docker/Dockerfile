FROM docker:28-dind

ARG VERSION
ENV DOCKER_TAG=${VERSION}

RUN apk update && \
	apk add \
	bash \
	curl \
	jq \
	gcc \
	gettext \
	git \
	libc-dev \
	libffi-dev \
	make \
	openssl-dev \
	py3-cryptography \
	py3-pip \
	python3 \
	python3-dev

RUN pip install --upgrade --break-system-packages --no-cache \
	awscli \
	"datadog==0.35.0" \
	"pyjwt>=1.6.0" \
	"https://github.com/skip-pay/developers-chamber/archive/refs/tags/${DOCKER_TAG}.tar.gz"

ENTRYPOINT ["bash", "-c"]
