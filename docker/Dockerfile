FROM docker:29-dind

ARG VERSION
ENV DOCKER_TAG=${VERSION}

RUN apk update && \
	apk add \
	bash \
	curl \
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

RUN pip install --upgrade --break-system-packages \
	pip \
	setuptools

RUN pip install --upgrade --break-system-packages \
	awscli \
	"datadog==0.35.0" \
	"pyjwt>=1.6.0" \
	"developers-chamber[git,gitlab,jira,slack,aws]==${DOCKER_TAG}"

ENTRYPOINT ["bash", "-c"]
