FROM docker:20.10

ARG VERSION
ENV DOCKER_TAG=${VERSION}

RUN apk update && \
	apk add \
	bash \
	gcc \
	gettext \
	git \
	libc-dev \
	libffi-dev \
	make \
	openssh \
	openssl-dev \
	openssl-dev \
	python3 \
	python3-dev \
	py3-cryptography \
	py3-pip

RUN pip install --upgrade \
	pip \
	setuptools

RUN pip install --upgrade \
	awscli \
	"datadog==0.35.0" \
	"docker-compose==1.29.1" \
	"pyjwt>=1.6.0" \
	"https://github.com/druids/developers-chamber/tarball/${DOCKER_TAG}"

ENTRYPOINT ["bash", "-c"]
