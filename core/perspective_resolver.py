#!/usr/bin/env python3
"""
perspective_resolver.py - Core resolver for flipped perspective v1.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple


ResolverErrorCode = Literal[
    "not_found",
    "denied",
    "invalid_path",
    "ambiguous",
    "conflict",
    "unsupported",
    "io_error",
]

NodeType = Literal["file", "dir", "missing", "virtual_anchor"]
CreateNodeType = Literal["file", "dir"]


@dataclass(frozen=True)
class PerspectiveContext:
    perspective_id: str
    project_root: str
    cpd: str
    cwd_real: str
    role: Optional[str] = None
    template_head: Tuple[str, ...] = ()
    acl_checker: Optional[Callable[[Optional[str], Path, str], bool]] = None


@dataclass(frozen=True)
class ResolveResult:
    ok: bool
    cpd: str
    real_path: Optional[str]
    node_type: NodeType
    error_code: Optional[ResolverErrorCode] = None
    message: Optional[str] = None


@dataclass(frozen=True)
class ParsedCpd:
    template_parts: Tuple[str, ...]
    project_name: Optional[str]
    tail_parts: Tuple[str, ...]
    is_projects_anchor: bool


def perspective_open(
    *,
    perspective_id: str,
    project_root: str,
    start_real_path: str,
    role: str | None = None,
) -> PerspectiveContext:
    root = Path(project_root).expanduser().resolve()
    start = Path(start_real_path).expanduser().resolve()
    if perspective_id != "flipped":
        raise ValueError("Only flipped perspective is supported in v1")
    if not root.exists() or not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    if not start.exists():
        raise ValueError("start_real_path does not exist")
    if not _is_within(start, root):
        raise ValueError("start_real_path must be within project_root")

    rel = start.relative_to(root)
    parts = rel.parts
    if len(parts) == 0:
        raise ValueError("start_real_path must point into a project branch")

    project_name = parts[0]
    template_head: Tuple[str, ...] = tuple(parts[1:])
    cpd = _build_cpd(template_head, project_name, ())

    return PerspectiveContext(
        perspective_id=perspective_id,
        project_root=str(root),
        cpd=cpd,
        cwd_real=str(start),
        role=role,
        template_head=template_head,
        acl_checker=None,
    )


def resolve_virtual_path(
    *,
    ctx: PerspectiveContext,
    cpd: str,
) -> ResolveResult:
    cpd_norm = _normalize_cpd(cpd)
    parsed = _parse_cpd(cpd_norm)
    if parsed is None:
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="invalid CPD format",
        )

    if parsed.is_projects_anchor:
        return ResolveResult(
            ok=True,
            cpd=cpd_norm,
            real_path=None,
            node_type="virtual_anchor",
            error_code=None,
            message=None,
        )

    if parsed.project_name is None:
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="missing project segment",
        )

    real_path = _to_real_path(ctx, parsed)
    if not _is_within(real_path, Path(ctx.project_root)):
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="resolved path escapes project_root",
        )

    if _is_denied(ctx, real_path, "read"):
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=str(real_path),
            node_type="missing",
            error_code="denied",
            message="read denied",
        )

    if not real_path.exists():
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=str(real_path),
            node_type="missing",
            error_code="not_found",
            message="path does not exist",
        )

    node_type: NodeType = "dir" if real_path.is_dir() else "file"
    return ResolveResult(
        ok=True,
        cpd=cpd_norm,
        real_path=str(real_path),
        node_type=node_type,
        error_code=None,
        message=None,
    )


def resolve_real_path(
    *,
    ctx: PerspectiveContext,
    real_path: str,
) -> ResolveResult:
    path = Path(real_path).expanduser().resolve()
    root = Path(ctx.project_root)

    if not _is_within(path, root):
        return ResolveResult(
            ok=False,
            cpd=ctx.cpd,
            real_path=str(path),
            node_type="missing",
            error_code="invalid_path",
            message="real_path must be within project_root",
        )

    rel = path.relative_to(root)
    if len(rel.parts) == 0:
        return ResolveResult(
            ok=False,
            cpd="/",
            real_path=str(path),
            node_type="virtual_anchor",
            error_code="unsupported",
            message="project root has no flipped CPD mapping",
        )

    project_name = rel.parts[0]
    remainder = rel.parts[1:]
    template_head = tuple(ctx.template_head)

    if template_head and tuple(remainder[: len(template_head)]) != template_head:
        return ResolveResult(
            ok=False,
            cpd=ctx.cpd,
            real_path=str(path),
            node_type="missing",
            error_code="ambiguous",
            message="real path does not align with context template head",
        )

    tail = tuple(remainder[len(template_head) :]) if len(remainder) >= len(template_head) else ()
    cpd = _build_cpd(template_head, project_name, tail)

    node_type: NodeType
    if path.exists():
        node_type = "dir" if path.is_dir() else "file"
    else:
        node_type = "missing"
    return ResolveResult(
        ok=path.exists(),
        cpd=cpd,
        real_path=str(path),
        node_type=node_type,
        error_code=None if path.exists() else "not_found",
        message=None if path.exists() else "path does not exist",
    )


def list_virtual_dir(
    *,
    ctx: PerspectiveContext,
    cpd: str,
) -> List[Dict[str, object]]:
    cpd_norm = _normalize_cpd(cpd)
    parsed = _parse_cpd(cpd_norm)
    if parsed is None:
        return []

    entries: List[Dict[str, object]] = []

    if parsed.is_projects_anchor:
        root = Path(ctx.project_root)
        for project in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
            child_cpd = _build_cpd(parsed.template_parts, project.name, ())
            entries.append(
                {
                    "name": project.name,
                    "cpd": child_cpd,
                    "nodeType": "dir",
                    "realPath": str(project),
                    "isVirtual": True,
                }
            )
        return entries

    resolved = resolve_virtual_path(ctx=ctx, cpd=cpd_norm)
    if not resolved.ok or resolved.node_type != "dir" or not resolved.real_path:
        return []

    parent = Path(resolved.real_path)
    for child in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
        child_cpd = _join_cpd(cpd_norm, child.name)
        entries.append(
            {
                "name": child.name,
                "cpd": child_cpd,
                "nodeType": "dir" if child.is_dir() else "file",
                "realPath": str(child),
                "isVirtual": False,
            }
        )
    return entries


def prepare_create(
    *,
    ctx: PerspectiveContext,
    cpd_parent: str,
    name: str,
    node_type: CreateNodeType,
) -> ResolveResult:
    if node_type not in {"file", "dir"}:
        return ResolveResult(
            ok=False,
            cpd=_normalize_cpd(cpd_parent),
            real_path=None,
            node_type="missing",
            error_code="unsupported",
            message="unsupported create node type",
        )

    if not name or "/" in name or name == "." or name == "..":
        return ResolveResult(
            ok=False,
            cpd=_normalize_cpd(cpd_parent),
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="invalid child name",
        )

    parent = resolve_virtual_path(ctx=ctx, cpd=cpd_parent)
    if not parent.ok or parent.node_type != "dir" or not parent.real_path:
        return ResolveResult(
            ok=False,
            cpd=parent.cpd,
            real_path=parent.real_path,
            node_type="missing",
            error_code=parent.error_code or "not_found",
            message="parent not available",
        )

    parent_path = Path(parent.real_path)
    if _is_denied(ctx, parent_path, "write"):
        return ResolveResult(
            ok=False,
            cpd=parent.cpd,
            real_path=str(parent_path),
            node_type="missing",
            error_code="denied",
            message="write denied",
        )

    target = (parent_path / name).resolve()
    if not _is_within(target, Path(ctx.project_root)):
        return ResolveResult(
            ok=False,
            cpd=parent.cpd,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="target escapes project_root",
        )
    if target.exists():
        return ResolveResult(
            ok=False,
            cpd=_join_cpd(parent.cpd, name),
            real_path=str(target),
            node_type="missing",
            error_code="conflict",
            message="target already exists",
        )

    return ResolveResult(
        ok=True,
        cpd=_join_cpd(parent.cpd, name),
        real_path=str(target),
        node_type="missing",
        error_code=None,
        message=None,
    )


def prepare_rename(
    *,
    ctx: PerspectiveContext,
    source_cpd: str,
    target_parent_cpd: str,
    target_name: str,
) -> Tuple[ResolveResult, ResolveResult]:
    source_parsed = _parse_cpd(_normalize_cpd(source_cpd))
    target_parsed = _parse_cpd(_normalize_cpd(target_parent_cpd))
    if source_parsed is None or target_parsed is None:
        source = resolve_virtual_path(ctx=ctx, cpd=source_cpd)
        return source, ResolveResult(
            ok=False,
            cpd=_normalize_cpd(target_parent_cpd),
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="invalid CPD for rename",
        )
    if source_parsed.project_name != target_parsed.project_name:
        source = resolve_virtual_path(ctx=ctx, cpd=source_cpd)
        return source, ResolveResult(
            ok=False,
            cpd=_normalize_cpd(target_parent_cpd),
            real_path=None,
            node_type="missing",
            error_code="unsupported",
            message="cross-project rename unsupported in v1",
        )

    source = resolve_virtual_path(ctx=ctx, cpd=source_cpd)
    if not source.ok:
        return source, ResolveResult(
            ok=False,
            cpd=_normalize_cpd(target_parent_cpd),
            real_path=None,
            node_type="missing",
            error_code="not_found",
            message="source unresolved",
        )

    target_parent = resolve_virtual_path(ctx=ctx, cpd=target_parent_cpd)
    if not target_parent.ok or target_parent.node_type != "dir" or not target_parent.real_path:
        return source, ResolveResult(
            ok=False,
            cpd=target_parent.cpd,
            real_path=target_parent.real_path,
            node_type="missing",
            error_code=target_parent.error_code or "not_found",
            message="target parent unresolved",
        )

    if _is_denied(ctx, Path(source.real_path or ""), "write") or _is_denied(ctx, Path(target_parent.real_path), "write"):
        return source, ResolveResult(
            ok=False,
            cpd=target_parent.cpd,
            real_path=target_parent.real_path,
            node_type="missing",
            error_code="denied",
            message="write denied",
        )

    if not target_name or "/" in target_name or target_name in {".", ".."}:
        return source, ResolveResult(
            ok=False,
            cpd=target_parent.cpd,
            real_path=target_parent.real_path,
            node_type="missing",
            error_code="invalid_path",
            message="invalid target name",
        )

    target_real = (Path(target_parent.real_path) / target_name).resolve()
    if target_real.exists():
        return source, ResolveResult(
            ok=False,
            cpd=_join_cpd(target_parent.cpd, target_name),
            real_path=str(target_real),
            node_type="missing",
            error_code="conflict",
            message="target already exists",
        )

    return source, ResolveResult(
        ok=True,
        cpd=_join_cpd(target_parent.cpd, target_name),
        real_path=str(target_real),
        node_type="missing",
        error_code=None,
        message=None,
    )


def _is_denied(ctx: PerspectiveContext, path: Path, action: str) -> bool:
    if str(ctx.role or "").strip().lower() == "deny":
        return True
    checker = ctx.acl_checker
    if checker is None:
        return False
    try:
        return not bool(checker(ctx.role, path, action))
    except Exception:
        return True


def _normalize_cpd(cpd: str) -> str:
    raw = str(cpd or "").strip()
    if not raw:
        return "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    parts: List[str] = []
    for part in raw.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            return "/../invalid"
        parts.append(part)
    return "/" + "/".join(parts) if parts else "/"


def _parse_cpd(cpd: str) -> Optional[ParsedCpd]:
    if cpd.startswith("/../"):
        return None
    parts = tuple(p for p in cpd.strip("/").split("/") if p)
    if not parts:
        return ParsedCpd(template_parts=(), project_name=None, tail_parts=(), is_projects_anchor=True)

    projects_positions = [idx for idx, part in enumerate(parts) if part == "Projekte"]
    if len(projects_positions) != 1:
        return None

    idx = projects_positions[0]
    template_parts = parts[:idx]
    if idx == len(parts) - 1:
        return ParsedCpd(
            template_parts=template_parts,
            project_name=None,
            tail_parts=(),
            is_projects_anchor=True,
        )

    project_name = parts[idx + 1]
    if not project_name:
        return None
    tail = parts[idx + 2 :]
    return ParsedCpd(
        template_parts=template_parts,
        project_name=project_name,
        tail_parts=tail,
        is_projects_anchor=False,
    )


def _to_real_path(ctx: PerspectiveContext, parsed: ParsedCpd) -> Path:
    assert parsed.project_name is not None
    root = Path(ctx.project_root)
    return (root / parsed.project_name / Path(*parsed.template_parts) / Path(*parsed.tail_parts)).resolve()


def _build_cpd(template_parts: Sequence[str], project_name: str, tail_parts: Sequence[str]) -> str:
    pieces = list(template_parts) + ["Projekte", project_name] + list(tail_parts)
    return "/" + "/".join([p for p in pieces if p])


def _join_cpd(parent: str, child_name: str) -> str:
    parent_norm = _normalize_cpd(parent).rstrip("/")
    if not parent_norm:
        parent_norm = "/"
    if parent_norm == "/":
        return f"/{child_name}"
    return f"{parent_norm}/{child_name}"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
