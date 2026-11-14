#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET_DIR="${HOME}/.local/share/thumbnailers"
TARGET_FILE="${TARGET_DIR}/seiton-md.thumbnailer"
SRC_FILE="${REPO_ROOT}/installer/seiton-md.thumbnailer"
# The same definition under the former name (MyOS): taken away, or it would render twice.
LEGACY_FILES=("${TARGET_DIR}/myos-md.thumbnailer" "${TARGET_DIR}/myos-markdown.thumbnailer")
ACTION="${1:-install}"

die() {
    echo "Error: $*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage:
  ./installer/install-thumbnailer.sh [install|check|uninstall]

Commands:
  install    Install/update user thumbnailer definition (default)
  check      Validate current thumbnailer installation
  uninstall  Remove user thumbnailer definition
EOF
}

ensure_prerequisites() {
    command -v python3 >/dev/null 2>&1 || die "python3 not found in PATH"
    [ -f "${SRC_FILE}" ] || die "missing template: ${SRC_FILE}"
    [ -f "${REPO_ROOT}/scripts/seiton_md_thumbnailer.py" ] || die "missing renderer script in scripts/"
}

install_thumbnailer() {
    ensure_prerequisites
    mkdir -p "${TARGET_DIR}"

    tmp_file="$(mktemp)"
    sed "s|__REPO_ROOT__|${REPO_ROOT}|g" "${SRC_FILE}" > "${tmp_file}"

    if [ -f "${TARGET_FILE}" ] && cmp -s "${tmp_file}" "${TARGET_FILE}"; then
        rm -f "${tmp_file}"
        echo "Thumbnailer already up-to-date:"
        echo "  ${TARGET_FILE}"
    else
        install -m 0644 "${tmp_file}" "${TARGET_FILE}"
        rm -f "${tmp_file}"
        echo "Installed thumbnailer definition:"
        echo "  ${TARGET_FILE}"
    fi

    chmod +x "${REPO_ROOT}/scripts/seiton_md_thumbnailer.py" || true
    remove_former
    echo
    echo "Quick check:"
    "${BASH_SOURCE[0]}" check
    echo
    echo "Recommended cache refresh:"
    echo "  rm -rf \"${HOME}/.cache/thumbnails\"/*"
    echo "Then reopen your file browser."
}

check_thumbnailer() {
    if [ ! -f "${TARGET_FILE}" ]; then
        die "thumbnailer file not installed: ${TARGET_FILE}"
    fi

    exec_line="$(awk -F= '/^Exec=/{print substr($0,6)}' "${TARGET_FILE}" | head -n 1)"
    [ -n "${exec_line}" ] || die "no Exec line in ${TARGET_FILE}"

    echo "Thumbnailer file:"
    echo "  ${TARGET_FILE}"
    echo "Exec:"
    echo "  ${exec_line}"

    if [[ "${exec_line}" == *"scripts/seiton_md_thumbnailer.py"* ]]; then
        script_path="$(echo "${exec_line}" | awk '{print $2}')"
        [ -f "${script_path}" ] || die "renderer script referenced by Exec not found: ${script_path}"
        echo "Renderer script:"
        echo "  ${script_path}"
    fi

    echo "Status: OK"
}

remove_former() {
    for old in "${LEGACY_FILES[@]}"; do
        if [ -f "${old}" ]; then
            rm -f "${old}"
            echo "Removed former definition:"
            echo "  ${old}"
        fi
    done
}

uninstall_thumbnailer() {
    remove_former
    if [ -f "${TARGET_FILE}" ]; then
        rm -f "${TARGET_FILE}"
        echo "Removed thumbnailer definition:"
        echo "  ${TARGET_FILE}"
    else
        echo "Nothing to remove. File not found:"
        echo "  ${TARGET_FILE}"
    fi
}

case "${ACTION}" in
    install)
        install_thumbnailer
        ;;
    check)
        check_thumbnailer
        ;;
    uninstall)
        uninstall_thumbnailer
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        die "unknown action: ${ACTION}"
        ;;
esac
