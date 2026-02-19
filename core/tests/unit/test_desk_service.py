from pathlib import Path

from core.desk_service import DeskService


class _FakeRuntime:
    def __init__(self) -> None:
        self.calls = []

    def handle_context(self, path, manual_desk=None):
        self.calls.append((str(path), str(manual_desk) if manual_desk else None))
        return {"ok": True, "applied": False, "reason": "fake", "source": None, "steps": []}

    def get_active_profile(self):
        return {"source": "fake-source", "hash": "fake-hash"}


def test_desk_service_refresh_context_and_getters(tmp_path):
    runtime = _FakeRuntime()
    service = DeskService(runtime=runtime)
    folder = tmp_path / "Project"
    folder.mkdir(parents=True)

    result = service.refresh_context(folder)

    assert result["ok"] is True
    assert result["reason"] == "fake"
    assert service.get_active_profile()["source"] == "fake-source"
    assert service.get_last_result()["reason"] == "fake"
    assert runtime.calls


def test_desk_service_find_config_nearest_ancestor(tmp_path):
    project = tmp_path / "Project"
    sub = project / "Sub"
    sub.mkdir(parents=True)
    cfg = project / ".MyOS" / "Desk.md"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("# Desk\nThemePreset: Demo\n", encoding="utf-8")
    service = DeskService(runtime=_FakeRuntime())

    found = service.find_config(sub)

    assert found == cfg


def test_desk_service_rejects_unsafe_config_name_for_security(tmp_path):
    project = tmp_path / "Project"
    project.mkdir(parents=True)
    service = DeskService(runtime=_FakeRuntime())

    found = service.find_config(project, config_name="../steal.md")
    targets = service.list_config_targets(project, config_name="../steal.md")

    assert found is None
    assert len(targets) == 1
    assert targets[0]["id"] == "discard"


def test_desk_service_rejects_overlong_config_name_for_security(tmp_path):
    project = tmp_path / "Project"
    project.mkdir(parents=True)
    service = DeskService(runtime=_FakeRuntime())
    long_name = "A" * 200 + ".md"

    found = service.find_config(project, config_name=long_name)
    targets = service.list_config_targets(project, config_name=long_name)

    assert found is None
    assert len(targets) == 1
    assert targets[0]["id"] == "discard"


def test_desk_service_rejects_non_ascii_spoofed_config_name_for_security(tmp_path):
    project = tmp_path / "Project"
    project.mkdir(parents=True)
    service = DeskService(runtime=_FakeRuntime())
    spoofed = "Dеsk.md"  # Cyrillic e

    found = service.find_config(project, config_name=spoofed)
    targets = service.list_config_targets(project, config_name=spoofed)

    assert found is None
    assert len(targets) == 1
    assert targets[0]["id"] == "discard"
