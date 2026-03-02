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
    effective_read_path: Optional[str] = None
    fallback_applied: bool = False
    fallback_from: Optional[str] = None
    fallback_to: Optional[str] = None


@dataclass(frozen=True)
class ParsedCpd:
    template_parts: Tuple[str, ...]
    project_name: Optional[str]
    tail_parts: Tuple[str, ...]
    is_projects_anchor: bool


@dataclass(frozen=True)
class ParsedMergedTemplatesCpd:
    valid: bool
    cpd: str
    project_name: Optional[str]
    template_hint: Optional[str]
    tail_parts: Tuple[str, ...]
    is_off: bool


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
        # CWD at project_root (e.g. "Projekte" container) is valid: open with projects anchor.
        project_name = ""
        template_head = ()
        cpd = "/Projekte"
    else:
        project_name = parts[0]
        template_head = tuple(parts[1:])
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


def perspective_open_from_cpd(
    *,
    project_root: str,
    cpd: str,
    perspective_id: str = "flipped",
    role: str | None = None,
) -> PerspectiveContext:
    """
    Create a PerspectiveContext from (project_root, cpd) instead of start_real_path.
    CPD must be in canonical form (containing \"Projekte\"). For projects anchor,
    start_real_path is project_root; otherwise it is derived from parsed path segments.
    """
    root = Path(project_root).expanduser().resolve()
    if perspective_id != "flipped":
        raise ValueError("Only flipped perspective is supported in v1")
    if not root.exists() or not root.is_dir():
        raise ValueError("project_root must be an existing directory")

    cpd_norm = _normalize_cpd(cpd)
    parsed = _parse_cpd(cpd_norm)
    if parsed is None:
        raise ValueError("invalid CPD: cannot parse")

    if parsed.is_projects_anchor or parsed.project_name is None:
        start_real_path = str(root)
    else:
        start = (
            root
            / parsed.project_name
            / Path(*parsed.template_parts)
            / Path(*parsed.tail_parts)
        ).resolve()
        start_real_path = str(start)

    return perspective_open(
        perspective_id=perspective_id,
        project_root=project_root,
        start_real_path=start_real_path,
        role=role,
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
            effective_read_path=None,
        )

    if parsed.is_projects_anchor:
        return ResolveResult(
            ok=True,
            cpd=cpd_norm,
            real_path=None,
            node_type="virtual_anchor",
            error_code=None,
            message=None,
            effective_read_path=None,
        )

    if parsed.project_name is None:
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="missing project segment",
            effective_read_path=None,
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
            effective_read_path=None,
        )

    if _is_denied(ctx, real_path, "read"):
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=str(real_path),
            node_type="missing",
            error_code="denied",
            message="read denied",
            effective_read_path=None,
        )

    if not real_path.exists():
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=str(real_path),
            node_type="missing",
            error_code="not_found",
            message="path does not exist",
            effective_read_path=None,
        )

    node_type: NodeType = "dir" if real_path.is_dir() else "file"
    return ResolveResult(
        ok=True,
        cpd=cpd_norm,
        real_path=str(real_path),
        node_type=node_type,
        error_code=None,
        message=None,
        effective_read_path=str(real_path),
    )


def resolve_virtual_dir_for_read(
    *,
    ctx: PerspectiveContext,
    cpd: str,
) -> ResolveResult:
    """
    Resolve a CPD for directory-read semantics.

    If the canonical CPD directory does not physically exist yet, fall back to
    the nearest existing parent in the same project branch. File reads remain
    strict via resolve_virtual_path().
    """
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
            effective_read_path=None,
        )
    if parsed.is_projects_anchor:
        return ResolveResult(
            ok=True,
            cpd=cpd_norm,
            real_path=None,
            node_type="virtual_anchor",
            error_code=None,
            message=None,
            effective_read_path=None,
        )
    if parsed.project_name is None:
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="missing project segment",
            effective_read_path=None,
        )

    root = Path(ctx.project_root)
    canonical = _to_real_path(ctx, parsed)
    if not _is_within(canonical, root):
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=None,
            node_type="missing",
            error_code="invalid_path",
            message="resolved path escapes project_root",
            effective_read_path=None,
        )
    if _is_denied(ctx, canonical, "read"):
        return ResolveResult(
            ok=False,
            cpd=cpd_norm,
            real_path=str(canonical),
            node_type="missing",
            error_code="denied",
            message="read denied",
            effective_read_path=None,
        )

    if canonical.exists():
        node_type: NodeType = "dir" if canonical.is_dir() else "file"
        return ResolveResult(
            ok=True,
            cpd=cpd_norm,
            real_path=str(canonical),
            node_type=node_type,
            error_code=None,
            message=None,
            effective_read_path=str(canonical),
            fallback_applied=False,
        )

    # Parent fallback for directory reads: walk up only within the same project.
    # Walk over the full branch path (template + tail), so missing template
    # segments can still fall back to existing project parents.
    branch_parts = list(parsed.template_parts + parsed.tail_parts)
    template_len = len(parsed.template_parts)
    current = canonical
    while branch_parts:
        current = current.parent
        branch_parts.pop()
        if not _is_within(current, root):
            break
        if _is_denied(ctx, current, "read"):
            return ResolveResult(
                ok=False,
                cpd=cpd_norm,
                real_path=str(canonical),
                node_type="missing",
                error_code="denied",
                message="read denied on fallback path",
                effective_read_path=None,
            )
        if current.exists() and current.is_dir():
            remaining_template_len = min(template_len, len(branch_parts))
            fallback_template = tuple(branch_parts[:remaining_template_len])
            fallback_tail = tuple(branch_parts[remaining_template_len:])
            fallback_to = _build_cpd(fallback_template, parsed.project_name, fallback_tail)
            return ResolveResult(
                ok=True,
                cpd=cpd_norm,
                real_path=str(canonical),
                node_type="dir",
                error_code=None,
                message=None,
                effective_read_path=str(current),
                fallback_applied=True,
                fallback_from=cpd_norm,
                fallback_to=fallback_to,
            )

    return ResolveResult(
        ok=False,
        cpd=cpd_norm,
        real_path=str(canonical),
        node_type="missing",
        error_code="not_found",
        message="path does not exist",
        effective_read_path=None,
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

    resolved = resolve_virtual_dir_for_read(ctx=ctx, cpd=cpd_norm)
    if not resolved.ok or resolved.node_type != "dir":
        return []

    if not resolved.effective_read_path:
        return []
    parent = Path(resolved.effective_read_path)
    listing_cpd = str(resolved.fallback_to or cpd_norm)
    for child in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
        child_cpd = _join_cpd(listing_cpd, child.name)
        entries.append(
            {
                "name": child.name,
                "cpd": child_cpd,
                "nodeType": "dir" if child.is_dir() else "file",
                "realPath": str(child),
                "isVirtual": bool(resolved.fallback_applied),
                "fallbackApplied": bool(resolved.fallback_applied),
            }
        )
    return entries


def parse_merged_templates_cpd(
    *,
    cpd: str,
    fallback_project_name: Optional[str] = None,
    fallback_template_hint: Optional[str] = None,
) -> ParsedMergedTemplatesCpd:
    """
    Parse CPD for merged template listing semantics.

    - Canonical OFF anchor: /Templates (project inferred from fallback).
    - Flipped CPD format keeps the template segment as hint only.
    """
    cpd_norm = _normalize_cpd(cpd)
    if cpd_norm.startswith("/../"):
        return ParsedMergedTemplatesCpd(
            valid=False,
            cpd=cpd_norm,
            project_name=None,
            template_hint=None,
            tail_parts=(),
            is_off=False,
        )

    if cpd_norm in {"/Templates", "/Templates/"}:
        project_name = str(fallback_project_name or "").strip() or None
        template_hint = str(fallback_template_hint or "").strip() or None
        return ParsedMergedTemplatesCpd(
            valid=project_name is not None,
            cpd="/Templates",
            project_name=project_name,
            template_hint=template_hint,
            tail_parts=(),
            is_off=True,
        )
    if cpd_norm.startswith("/Templates/"):
        project_name = str(fallback_project_name or "").strip() or None
        tail_with_hint = [part for part in cpd_norm.split("/")[2:] if part]
        template_hint = str(tail_with_hint[0] or "").strip() if tail_with_hint else ""
        if not template_hint:
            template_hint = str(fallback_template_hint or "").strip()
        template_hint = template_hint or None
        tail = tuple(tail_with_hint[1:]) if tail_with_hint else ()
        return ParsedMergedTemplatesCpd(
            valid=project_name is not None,
            cpd=cpd_norm,
            project_name=project_name,
            template_hint=template_hint,
            tail_parts=tail,
            is_off=(len(tail) == 0),
        )

    parsed = _parse_cpd(cpd_norm)
    if parsed is None or parsed.project_name is None:
        return ParsedMergedTemplatesCpd(
            valid=False,
            cpd=cpd_norm,
            project_name=None,
            template_hint=None,
            tail_parts=(),
            is_off=False,
        )

    template_parts = list(parsed.template_parts)
    template_hint: Optional[str] = None
    merged_tail: List[str] = []
    if template_parts:
        if template_parts[0] == "Templates":
            if len(template_parts) > 1:
                template_hint = str(template_parts[1] or "")
                merged_tail.extend(str(part) for part in template_parts[2:])
        else:
            template_hint = str(template_parts[0] or "")
            merged_tail.extend(str(part) for part in template_parts[1:])
    merged_tail.extend(str(part) for part in parsed.tail_parts)
    merged_tail = [part for part in merged_tail if part]

    if not template_hint:
        template_hint = str(fallback_template_hint or "").strip() or None

    return ParsedMergedTemplatesCpd(
        valid=True,
        cpd=cpd_norm,
        project_name=str(parsed.project_name),
        template_hint=template_hint,
        tail_parts=tuple(merged_tail),
        is_off=False,
    )


def build_hint_cpd(
    *,
    project_name: str,
    template_hint: str,
    tail_parts: Sequence[str],
) -> str:
    safe_project = str(project_name or "").strip()
    safe_hint = str(template_hint or "").strip()
    parts = [str(part) for part in tail_parts if str(part)]
    if safe_project == "" or safe_hint == "":
        return "/Templates"
    return _build_cpd([safe_hint], safe_project, parts)


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
