"""ACLs.md may be laid out freely: blank lines, notes and comments inside a role section
must not end the section and silently drop the rules below them (a dropped `none` would
open a locked folder). See "Designdocument ACLs.md", 2.3."""

from pathlib import Path

import pytest

from core.acl import ACLPolicy

HEAD = "# Permissions\n\n## Team\n- /Arbeit/: read, write\n"
LOCK = "- /Arbeit/Geheim/: none\n"
TAIL = "\n## Gast\n- /Info/: read\n\n# Users\nKarl: Team\nMia: Gast\n"


def _policy(tmp_path: Path, between: str) -> ACLPolicy:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(HEAD + between + LOCK + TAIL)
    return ACLPolicy.from_project(root)


@pytest.mark.parametrize(
    "between",
    [
        "",
        "\n",
        "\n\n",
        "Geheimes nur für die Geschäftsleitung\n",
        "<!-- Sperre seit 2026 -->\n",
        "<!--\n- /Arbeit/Geheim/: read\nalter Stand\n-->\n",
        "- Hinweis ohne Regel\n",
        "\nNotiz\n\n",
    ],
    ids=["none", "blank", "two-blanks", "note", "comment", "multiline-comment", "list-note", "mixed"],
)
def test_rules_after_blank_lines_notes_and_comments_still_apply(tmp_path, between):
    policy = _policy(tmp_path, between)

    assert policy.rights_for("team", "/Arbeit/Geheim/x.md") == {"none"}
    assert policy.rights_for("team", "/Arbeit/x.md") == {"read", "write"}
    assert policy.rights_for("gast", "/Info/x.md") == {"read"}
    assert policy.roles_for_user("Karl") == {"team"}


def test_commented_out_rules_do_not_apply(tmp_path):
    policy = _policy(tmp_path, "<!-- - /Arbeit/Offen/: read -->\n")

    assert policy.rights_for("team", "/Arbeit/Offen/x.md") == {"read", "write"}


def test_inline_hash_comment_after_a_rule(tmp_path):
    policy = _policy(tmp_path, "")
    acls = tmp_path / "Project" / ".MyOS" / "ACLs.md"
    acls.write_text(acls.read_text().replace(LOCK, "- /Arbeit/Geheim/: none  # seit 2026 gesperrt\n"))

    assert ACLPolicy.from_project(tmp_path / "Project").rights_for("team", "/Arbeit/Geheim/x.md") == {"none"}


def test_users_after_a_blank_line_and_a_note(tmp_path):
    _policy(tmp_path, "")
    root = tmp_path / "Project"
    acls = root / ".MyOS" / "ACLs.md"
    acls.write_text(acls.read_text().replace("Karl: Team\n", "Karl: Team\n\nNeu seit Oktober\nTom: Gast\n"))

    policy = ACLPolicy.from_project(root)

    assert policy.roles_for_user("Tom") == {"gast"}
    assert policy.roles_for_user("Mia") == {"gast"}
