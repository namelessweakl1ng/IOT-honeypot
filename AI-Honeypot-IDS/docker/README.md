# Shared Docker resources

This folder is reserved for Docker resources shared across computers
(custom base images, shared networks, build helpers). Currently empty —
each container builds its own image from `python:3.11-slim` directly. If
you want a shared hardened base image, add a `Dockerfile.base` here and
reference it via `build: ../../docker/base` in the compose files.

## Reserved files (future)
- `Dockerfile.base` — hardened Python 3.11 base image with common deps
- `docker-bake.hcl` — Docker Buildx bake definition for parallel builds
