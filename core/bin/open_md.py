#!/usr/bin/env python3
"""
Open a markdown file in Obsidian single-page mode.
Fallback: open with system default editor.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote


VAULT_MARKER = ".obsidian"
REPO_ROOT = Path(__file__).resolve().parents[2]
POSTFIX_PATH = REPO_ROOT / "PostFix" / "main.py"
OBSIDIAN_CONFIG_PATHS = [
    Path("~/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json"),
    Path("~/.config/obsidian/obsidian.json"),
]


def find_vault_root(start_path: Path) -> Path | None:
    for parent in [start_path] + list(start_path.parents):
        if (parent / VAULT_MARKER).is_dir():
            return parent
    return None
def load_registered_vaults() -> list[Path]:
    for config_path in OBSIDIAN_CONFIG_PATHS:
        path = config_path.expanduser()
        if not path.exists():
            continue
        try:
            data = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            payload = json.loads(data)
        except ValueError:
            continue
        vaults = payload.get("vaults", {})
        roots = []
        for entry in vaults.values():
            vault_path = entry.get("path")
            if vault_path:
                roots.append(Path(vault_path).expanduser().resolve())
        if roots:
            return roots
    return []


def resolve_vault_root(file_path: Path) -> Path | None:
    debug = os.environ.get("MYOS_MD_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    env_root = os.environ.get("MYOS_VAULT_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        try:
            file_path.relative_to(candidate)
        except ValueError:
            pass
        else:
            if debug:
                print(f"[open_md] vault root from MYOS_VAULT_ROOT: {candidate}")
            return candidate

    registered = load_registered_vaults()
    if registered:
        best = None
        for root in registered:
            try:
                file_path.relative_to(root)
            except ValueError:
                continue
            if best is None or len(str(root)) > len(str(best)):
                best = root
        if best is not None:
            if debug:
                print(f"[open_md] vault root from obsidian.json: {best}")
            return best

    fallback = find_vault_root(file_path.parent)
    if debug and fallback:
        print(f"[open_md] vault root from .obsidian scan: {fallback}")
    return fallback



def open_with_command(cmd: str, file_path: Path) -> int:
    args = shlex.split(cmd) + [str(file_path)]
    return subprocess.run(args, check=False).returncode


def open_with_xdg(target: str) -> int:
    return subprocess.run(["xdg-open", target], check=False).returncode


def open_with_postfix(file_path: Path) -> int:
    if POSTFIX_PATH.exists():
        return subprocess.run(
            [sys.executable, str(POSTFIX_PATH), str(file_path)], check=False
        ).returncode
    return open_with_xdg(str(file_path))


def build_advanced_uri(
    vault_root: Path,
    file_path: Path,
    open_mode: str,
    vault_name: str | None = None,
) -> str:
    vault_name = vault_name or vault_root.name
    rel_path = file_path.relative_to(vault_root).as_posix()
    vault_param = quote(vault_name)
    file_param = quote(rel_path)
    return f"obsidian://advanced-uri?vault={vault_param}&file={file_param}&openmode={open_mode}"


def build_native_uri(
    vault_root: Path,
    file_path: Path,
    vault_name: str | None = None,
) -> str:
    vault_name = vault_name or vault_root.name
    rel_path = file_path.relative_to(vault_root).as_posix()
    vault_param = quote(vault_name)
    file_param = quote(rel_path)
    return f"obsidian://open?vault={vault_param}&file={file_param}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open a .md file in Obsidian single-page mode."
    )
    parser.add_argument("path", help="Path to a .md file")
    parser.add_argument(
        "--openmode",
        choices=["window", "split", "tab"],
        default="window",
        help="Obsidian open mode (Advanced URI plugin required)",
    )
    parser.add_argument(
        "--uri-mode",
        choices=["native", "advanced"],
        help="Force Obsidian URI mode",
    )
    args = parser.parse_args()

    file_path = Path(args.path).expanduser().resolve()
    debug = os.environ.get("MYOS_MD_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    if debug:
        print(f"[open_md] file_path={file_path}")
    if not file_path.exists() or not file_path.is_file():
        print(f"File not found: {file_path}", file=sys.stderr)
        return 2
    if file_path.suffix.lower() != ".md":
        print(f"Not a markdown file: {file_path}", file=sys.stderr)
        return 2

    override_cmd = os.environ.get("MYOS_MD_EDITOR_CMD")
    force_override = os.environ.get("MYOS_MD_FORCE_EDITOR", "").strip().lower() in {"1", "true", "yes"}

    vault_root = resolve_vault_root(file_path)
    if vault_root:
        vault_name_override = os.environ.get("MYOS_VAULT_NAME")
        uri_mode = os.environ.get("MYOS_OBSIDIAN_URI_MODE", "native").strip().lower()
        if args.uri_mode:
            uri_mode = args.uri_mode
        debug = os.environ.get("MYOS_MD_DEBUG", "").strip().lower() in {"1", "true", "yes"}
        marker_path = vault_root / VAULT_MARKER / "myos-open.json"
        try:
            marker_path.write_text(
                json.dumps(
                    {"path": file_path.relative_to(vault_root).as_posix(), "ts": int(time.time())}
                ),
                encoding="utf-8",
            )
        except OSError:
            pass
        if uri_mode == "advanced":
            uri = build_advanced_uri(vault_root, file_path, args.openmode, vault_name_override)
        else:
            uri = build_native_uri(vault_root, file_path, vault_name_override)
        if debug:
            print(f"[open_md] uri_mode={uri_mode} uri={uri}")
        open_with_xdg(uri)
        return 0

    if override_cmd and force_override:
        return open_with_command(override_cmd, file_path)

    return open_with_postfix(file_path)


if __name__ == "__main__":
    raise SystemExit(main())
