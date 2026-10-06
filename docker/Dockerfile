FROM docker:29

ARG VERSION
ENV DOCKER_TAG=${VERSION}

LABEL org.opencontainers.image.source="https://github.com/druids/developers-chamber"
LABEL org.opencontainers.image.description="pydev (developers-chamber) with Docker, Helm, doctl and CI tooling"
LABEL org.opencontainers.image.licenses="MIT"

RUN apk update && \
	apk add \
	bash \
	coreutils \
	curl \
	doctl \
	expat \
	gcc \
	gettext \
	git \
	helm \
	jq \
	libc-dev \
	libffi-dev \
	make \
	openssl-dev \
	py3-cryptography \
	py3-pip \
	python3 \
	python3-dev \
	skopeo \
	zip

RUN pip install --upgrade --break-system-packages \
	pip \
	setuptools

RUN pip install --upgrade --break-system-packages \
	awscli \
	"datadog==0.35.0" \
	"pyjwt>=1.6.0" \
	pyhcl \
	ruamel.yaml \
	"developers-chamber[git,gitlab,jira,slack,aws]==${DOCKER_TAG}"

ENTRYPOINT ["bash", "-c"]
