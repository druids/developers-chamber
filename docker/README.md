# Docker image for developers-chamber

The image is published to the GitHub Container Registry on every release — the
`docker-build-n-publish` job in `.github/workflows/main.yml` runs after the PyPI upload and pushes
`linux/amd64` and `linux/arm64` variants:

```
docker pull ghcr.io/druids/developers-chamber:1.0.2
docker pull ghcr.io/druids/developers-chamber:latest
```

To build the docker image manually use the VERSION build argument to specify developers-chamber
version. The version is based on tags on github.

Example:
```
docker build --build-arg VERSION=1.0.2 -f docker/Dockerfile .
```
