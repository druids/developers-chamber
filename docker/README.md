# Docker image for developers-chamber

The image is published to the GitHub Container Registry on every release — the
`docker-build-n-publish` job in `.github/workflows/main.yml` runs after the PyPI upload and pushes
`linux/amd64` and `linux/arm64` variants.

Contains:
* docker, with the compose and buildx plugins
* pydev with the `git`, `gitlab`, `jira`, `slack` and `aws` extras
* doctl, helm, skopeo, jq, zip, coreutils, gettext
* awscli, datadog, pyhcl, ruamel.yaml

```
docker pull ghcr.io/druids/developers-chamber:1.0.4   # exact version
docker pull ghcr.io/druids/developers-chamber:1.0     # latest patch of 1.0
docker pull ghcr.io/druids/developers-chamber:1       # latest 1.x
docker pull ghcr.io/druids/developers-chamber:latest
```

To build the docker image manually use the VERSION build argument to specify developers-chamber
version. The version is based on tags on github.

Example:
```
docker build --build-arg VERSION=1.0.4 -f docker/Dockerfile .
```
