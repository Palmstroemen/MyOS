#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
HICOLOR_DIR="${ICONS_DIR}/hicolor"
EMBLEM_DIR="${REPO_ROOT}/assets/icons/emblems"
EMBLEM_LIGHT_DIR="${REPO_ROOT}/assets/icons/emblems-light"
FOLDER_SRC="${REPO_ROOT}/assets/icons/myos-folder-purple.svg"
FOLDER_DEST="${ICONS_DIR}/myos/myos-folder-purple.svg"

mkdir -p "$(dirname "${FOLDER_DEST}")"
mkdir -p "${HICOLOR_DIR}/scalable/emblems"

if [ -d "${EMBLEM_DIR}" ]; then
  cp "${EMBLEM_DIR}"/emblem-myos-*.svg "${HICOLOR_DIR}/scalable/emblems/"
fi
if [ -d "${EMBLEM_LIGHT_DIR}" ]; then
  cp "${EMBLEM_LIGHT_DIR}"/emblem-myos-*-light.svg "${HICOLOR_DIR}/scalable/emblems/"
fi
cp "${FOLDER_SRC}" "${FOLDER_DEST}"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "${HICOLOR_DIR}" || true
fi

echo "Installed emblems: ${HICOLOR_DIR}/scalable/emblems/emblem-myos-*.svg"
echo "Installed folder icon: ${FOLDER_DEST}"
echo ""
echo "Apply to folders:"
echo "  gio set -t stringv <folder> metadata::emblems emblem-myos-projekt"
echo "  gio set -t stringv <folder> metadata::emblems emblem-myos-finanz"
echo "  gio set -t string <folder> metadata::custom-icon \"file://${FOLDER_DEST}\""
