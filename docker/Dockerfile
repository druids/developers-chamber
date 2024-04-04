FROM docker:23-dind

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

RUN pip install --upgrade \
	pip \
	setuptools

RUN pip install --upgrade \
	awscli \
	"datadog==0.35.0" \
	"pyjwt>=1.6.0" \
	"https://github.com/skip-pay/developers-chamber/tarball/${DOCKER_TAG}"

ENTRYPOINT ["bash", "-c"]
