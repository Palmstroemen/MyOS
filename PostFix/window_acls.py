"""ACL sidebar behavior for PostFixWindow: who may access the open note."""

import os
from pathlib import Path

from core.acl_view import RIGHTS_ORDER, ACLView


def acl_principals_for_document(path: Path | None) -> list[dict]:
    """
    Roles, then users, with any right on the note at path, as
    {name, kind, rights (in RIGHTS_ORDER)}; [] without ACLs.md (none governs the note,
    also not inherited from a parent project) or when the viewer may not see them.
    """
    if not path:
        return []
    view = ACLView.for_path(path)
    if view is None:
        return []
    # Security: with enforcement on, only a user who may read ACLs.md sees its content
    # (same rule as Scope's ACL panel).
    # The viewer is determined as in ScopeApi (MYOS_ACL_USER, else $USER, else "local").
    mode = str(os.environ.get("MYOS_ACL_MODE") or "off").strip().lower()
    viewer = None
    if mode == "enforce":
        viewer = str(os.environ.get("MYOS_ACL_USER") or os.environ.get("USER") or "local").strip().lower()
    if not view.may_view(viewer):
        return []
    return [
        {"name": p.name, "kind": p.kind, "rights": [r for r in RIGHTS_ORDER if r in p.rights]}
        for p in view.principals(path)
    ]


class WindowAclsMixin:
    def _reload_acl_context(self):
        principals = acl_principals_for_document(getattr(self.editor, "current_path", None))
        self.left_sidebar.set_principals(principals)
        # Shown only when ACLs are in use for this note (simple first, power when used).
        self.acl_host.setVisible(bool(principals))
        self.acl_host.setFixedWidth(self.left_sidebar.preferred_width() if principals else 0)
