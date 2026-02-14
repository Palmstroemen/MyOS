#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MYOS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET_DIR="${HOME}/.local/share/thumbnailers"
TARGET_FILE="${TARGET_DIR}/myos-md.thumbnailer"
SRC_FILE="${MYOS_ROOT}/installer/myos-md.thumbnailer"

mkdir -p "${TARGET_DIR}"
sed "s|__MYOS_ROOT__|${MYOS_ROOT}|g" "${SRC_FILE}" > "${TARGET_FILE}"

echo "Installed thumbnailer definition:"
echo "  ${TARGET_FILE}"
echo
echo "Next step (recommended):"
echo "  rm -rf \"${HOME}/.cache/thumbnails\"/*"
echo "Then reopen your file browser."
