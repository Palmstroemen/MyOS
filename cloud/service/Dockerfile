# The Seiton core service ("cloud/nextcloud/Designdocument Seiton Core Service.md", 7): the core
# and its HTTP API, nothing else (no FUSE, no GUI, no packages beyond Python's own).
# Built from the repository root, for both architectures:
#   docker buildx build --platform linux/amd64,linux/arm64 -f cloud/service/Dockerfile -t seiton-core .
# Run with the shadow tree mounted read-only and the shared secret from the environment:
#   docker run -v /path/to/shadow:/shadow:ro -e SEITON_CORE_SECRET=... seiton-core
FROM python:3.12-slim

WORKDIR /opt/seiton
COPY core/ core/
COPY cloud/service/ cloud/service/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEITON_SHADOW_ROOT=/shadow \
    SEITON_CORE_HOST=0.0.0.0 \
    SEITON_CORE_PORT=8080

# Security: not as root; the service only reads.
RUN useradd --system --no-create-home seiton
USER seiton

EXPOSE 8080
CMD ["python3", "-m", "cloud.service.server"]
