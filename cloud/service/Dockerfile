# The MyOS core service ("cloud/nextcloud/Designdocument MyOS Core Service.md", 7): the core
# and its HTTP API, nothing else (no FUSE, no GUI, no packages beyond Python's own).
# Built from the repository root, for both architectures:
#   docker buildx build --platform linux/amd64,linux/arm64 -f cloud/service/Dockerfile -t myos-core .
# Run with the shadow tree mounted read-only and the shared secret from the environment:
#   docker run -v /path/to/shadow:/shadow:ro -e MYOS_CORE_SECRET=... myos-core
FROM python:3.12-slim

WORKDIR /opt/myos
COPY core/ core/
COPY cloud/service/ cloud/service/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MYOS_SHADOW_ROOT=/shadow \
    MYOS_CORE_HOST=0.0.0.0 \
    MYOS_CORE_PORT=8080

# Security: not as root; the service only reads.
RUN useradd --system --no-create-home myos
USER myos

EXPOSE 8080
CMD ["python3", "-m", "cloud.service.server"]
