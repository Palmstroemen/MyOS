"""ACL sidebar behavior for PostFixWindow: who may access the open note, and editing."""

import os
from pathlib import Path

from core.acl_edit import ACLEditError, ACLSelfLockoutError, can_edit, own_rule, set_role_rights, set_user_roles
from core.acl_view import RIGHTS_ORDER, ACLView
from core.identity import acl_user_for


def acl_principals_for_document(path: Path | None) -> list[dict]:
    """
    Roles, then users, with any right on the note at path, as
    {name, kind, key, rights (in RIGHTS_ORDER)}; [] without ACLs.md (none governs the note,
    also not inherited from a parent project) or when the viewer may not see them.
    """
    if not path:
        return []
    view = ACLView.for_path(path)
    if view is None:
        return []
    # Security: with enforcement on, only a user who may read ACLs.md sees its content
    # (same rule as Scope's ACL panel).
    mode = str(os.environ.get("MYOS_ACL_MODE") or "off").strip().lower()
    viewer = acl_user_for(path) if mode == "enforce" else None
    if not view.may_view(viewer):
        return []
    return [
        {"name": p.name, "kind": p.kind, "key": p.key, "rights": [r for r in RIGHTS_ORDER if r in p.rights]}
        for p in view.principals(path)
    ]


class WindowAclsMixin:
    def _reload_acl_context(self):
        path = getattr(self.editor, "current_path", None)
        principals = acl_principals_for_document(path)
        self.left_sidebar.set_principals(principals)
        # Security: chips only become editable for users with "change" on ACLs.md; the
        # core checks it again when writing.
        self.left_sidebar.set_editable(bool(principals) and can_edit(path, acl_user_for(path)))
        # Shown only when ACLs are in use for this note (simple first, power when used).
        self.acl_host.setVisible(bool(principals))
        self.acl_host.setFixedWidth(self.left_sidebar.preferred_width() if principals else 0)

    def _role_has_own_rule(self, role_key: str) -> bool:
        path = getattr(self.editor, "current_path", None)
        return bool(path) and own_rule(path, role_key) is not None

    def _apply_role_rights(self, role_key: str, rights) -> str:
        """
        Set role's rights on the open note (None: back to inherited). Returns "" on
        success, else a message for the user; the sidebar shows the new state.
        """
        path = getattr(self.editor, "current_path", None)
        if not path:
            return self.tr("No note is open.")
        return self._acl_edit(lambda: set_role_rights(
            path, role_key, None if rights is None else set(rights), editor=acl_user_for(path)))

    def _user_groups(self, user_key: str):
        """Groups of a person with what each may do with the open note (ACLView.user_groups)."""
        path = getattr(self.editor, "current_path", None)
        view = ACLView.for_path(path) if path else None
        return view.user_groups(user_key, path) if view is not None else None

    def _apply_user_groups(self, user_key: str, groups) -> str:
        """Set a person's groups (whole project); "" on success, else a message."""
        path = getattr(self.editor, "current_path", None)
        if not path:
            return self.tr("No note is open.")
        return self._acl_edit(lambda: set_user_roles(path, user_key, set(groups), editor=acl_user_for(path)))

    def _acl_edit(self, edit) -> str:
        """Run an ACLs.md edit; "" on success (the sidebar shows the new state), else a message."""
        try:
            edit()
        except PermissionError:
            return self.tr("You may not change the rights here.")
        except ACLSelfLockoutError:
            return self.tr("You would lose your own right to change the rights.")
        except (ACLEditError, OSError) as exc:
            return str(exc)
        self._reload_acl_context()
        return ""

    def _open_role_editor(self, role_key: str, role_name: str, rights, chip=None):
        """Rights editor for one group, next to its chip (sidebar: roleEditRequested)."""
        try:
            from .ui_panels import ACLRoleEditor
        except ImportError:
            from ui_panels import ACLRoleEditor
        editor = ACLRoleEditor(role_name, rights, own_rule=self._role_has_own_rule(role_key), parent=self)

        def apply(chosen):
            error = self._apply_role_rights(role_key, chosen)
            editor.show_error(error) if error else editor.close()

        editor.applyRequested.connect(apply)
        editor.resetRequested.connect(lambda: apply(None))
        if chip is not None:
            editor.move(chip.mapToGlobal(chip.rect().topRight()))
        self._acl_role_editor = editor  # keep it alive while open
        editor.show()

    def _open_person_editor(self, user_key: str, person_name: str, chip=None):
        """Groups editor for one person, next to their chip (sidebar: personEditRequested)."""
        try:
            from .ui_panels import ACLPersonEditor
        except ImportError:
            from ui_panels import ACLPersonEditor
        data = self._user_groups(user_key)
        if not data:
            return
        editor = ACLPersonEditor(data["name"], data["groups"], parent=self)

        def apply(chosen):
            error = self._apply_user_groups(user_key, chosen)
            editor.show_error(error) if error else editor.close()

        editor.applyRequested.connect(apply)
        if chip is not None:
            editor.move(chip.mapToGlobal(chip.rect().topRight()))
        self._acl_person_editor = editor  # keep it alive while open
        editor.show()
