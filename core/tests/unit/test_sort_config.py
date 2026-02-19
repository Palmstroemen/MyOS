from pathlib import Path

from core.sort import parse_sort_config, resolve_effective_sort_rules, validate_sort_rules


def test_parse_sort_config_reads_multiple_rules(tmp_path):
    project = tmp_path / "Project"
    cfg = project / ".MyOS" / "Sort.md"
    cfg.parent.mkdir(parents=True)
    (project / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    cfg.write_text(
        "\n".join(
            [
                "# Sort",
                "Root: /Pictures",
                "Pattern: {{YYYY}}/{{MM}}/{{DD}}",
                "",
                "# Sort",
                "Root: /Bills",
                "Pattern: {{YYYY}}/{{ABC}}",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rules = parse_sort_config(cfg)

    assert len(rules) == 2
    assert rules[0].root == "/Pictures"
    assert rules[0].pattern == "{{YYYY}}/{{MM}}/{{DD}}"
    assert rules[1].root == "/Bills"
    assert rules[1].pattern == "{{YYYY}}/{{ABC}}"


def test_validate_sort_rules_detects_duplicate_date_tokens(tmp_path):
    project = tmp_path / "Project"
    cfg = project / ".MyOS" / "Sort.md"
    cfg.parent.mkdir(parents=True)
    (project / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    cfg.write_text(
        "\n".join(
            [
                "# Sort",
                "Root: /Pictures",
                "Pattern: {{YYYY}}/archive/{{YYYY}}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rules = parse_sort_config(cfg)
    messages = validate_sort_rules(rules)

    assert any("duplicate date token" in msg for msg in messages)


def test_resolve_effective_sort_rules_prefers_nearest_parent(tmp_path):
    root = tmp_path / "Project"
    child = root / "Child"
    child.mkdir(parents=True)
    (root / ".MyOS").mkdir(parents=True)
    (child / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    (child / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    (root / ".MyOS" / "Sort.md").write_text(
        "# Sort\nRoot: /Pictures\nPattern: {{YYYY}}/{{MM}}\n",
        encoding="utf-8",
    )
    (child / ".MyOS" / "Sort.md").write_text(
        "# Sort\nRoot: /Pictures\nPattern: {{YYYY}}/{{ABC}}\n",
        encoding="utf-8",
    )

    rules = resolve_effective_sort_rules(child, config_name="Sort.md")

    assert len(rules) == 1
    assert rules[0].source_path == (child / ".MyOS" / "Sort.md")
    assert rules[0].pattern == "{{YYYY}}/{{ABC}}"
