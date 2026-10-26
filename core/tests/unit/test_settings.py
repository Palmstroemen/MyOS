"""The settings of MyOS's programs in one file (core/settings.py; Scope/Designdocument Setup.md):
Scope writes them on its back, SunTree reads them when it appears."""

from pathlib import Path

import pytest

from core.settings import Settings, settings_path


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    return tmp_path / "config"


def test_one_file_under_the_config_home(config):
    assert settings_path() == config / "MyOS" / "MyOS.conf"


def test_defaults_without_a_file(config):
    s = Settings()
    assert s.get("General/darkTheme") is True and s.get("General/language") == "de"
    assert s.get("SunTree/enter") == 0.75 and s.get("SunTree/leave") == 0.25
    assert s.group("SunTree")["lineT"] == 0.7


def test_a_change_is_kept_and_read_by_another(config):
    assert Settings().set("SunTree/enter", 0.8)
    assert Settings().get("SunTree/enter") == 0.8  # another program, the same file
    assert Settings().set("General/darkTheme", False)
    assert Settings().get("General/darkTheme") is False


def test_values_out_of_range_or_of_the_wrong_kind_are_refused(config):
    s = Settings()
    assert not s.set("SunTree/enter", 3.0)
    assert not s.set("General/language", "xx")
    assert not s.set("Nothing/such", 1)
    assert s.get("SunTree/enter") == 0.75


def test_a_hand_edited_file_falls_back_to_the_defaults(config):
    path = settings_path()
    path.parent.mkdir(parents=True)
    path.write_text("[SunTree]\nenter = lots\nleave = 0.9\nlineT = 0.6\n", encoding="utf-8")
    s = Settings()
    assert s.get("SunTree/enter") == 0.75  # not a number
    assert s.get("SunTree/leave") == 0.25  # out of range
    assert s.get("SunTree/lineT") == 0.6  # fine


def test_back_to_the_default(config):
    s = Settings()
    s.set("SunTree/lineT", 0.6)
    s.reset("SunTree/lineT")
    assert Settings().get("SunTree/lineT") == 0.7
    assert s.default("SunTree/lineT") == 0.7 and s.limits("SunTree/lineT") == (0.5, 0.85)


def test_how_pale_embryos_are_is_one_setting_for_all(config):
    s = Settings()
    assert s.get("General/embryoOpacity") == 0.4
    assert not s.set("General/embryoOpacity", 0.0)  # invisible: refused
    assert s.set("General/embryoOpacity", 0.6) and Settings().get("General/embryoOpacity") == 0.6


def test_the_badges_of_suggestions_have_their_own_setting(config):
    assert Settings().get("General/embryoBadgeOpacity") == 0.7  # half way to full


def test_the_rows_display_settings_for_both_browsers(config):
    s = Settings()
    assert s.get("Scope/pathBar") is True and s.get("Scope/preview") is True
    assert s.get("Scope/previewBackground") is False


def test_all_of_the_display_menu_moved_into_the_settings(config):
    s = Settings()
    assert s.get("Scope/projectsRow") is False  # off by default (2026-10-26)
    assert s.get("Scope/showSuggestions") is True and s.get("Scope/showHidden") is False
    assert s.get("Scope/templatesStyle") == "smallIcon" and s.get("Scope/projectsStyle") == "text"
    assert not s.set("Scope/templatesStyle", "huge")
    assert s.get("Scope/instantReopen") is True and s.get("Scope/previewTuning") == "balanced"
    assert not s.set("Scope/previewTuning", "wild")
