"""The back of Scope (Scope/SetupPage.qml; Scope/Designdocument Setup.md): tabs General, Scope,
Headline, SunTree; what is set there goes to the one settings file (core/settings.py)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


class SettingsHost(QObject):
    """What Scope's backend offers the back (Scope.py: setting, setSetting, ...)."""

    def __init__(self):
        super().__init__()
        from core.settings import Settings
        self.settings = Settings()

    @Slot(str, result="QVariant")
    def setting(self, key):
        return self.settings.get(key)

    @Slot(str, "QVariant", result=bool)
    def setSetting(self, key, value):
        return self.settings.set(key, value)

    @Slot(str, result="QVariant")
    def settingDefault(self, key):
        return self.settings.default(key)

    @Slot(str, result="QVariantList")
    def settingLimits(self, key):
        return list(self.settings.limits(key) or [])

    @Slot(str)
    def resetSetting(self, key):
        self.settings.reset(key)


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _named(view, name):
    return next((i for i in _walk(view.rootObject()) if i.objectName() == name), None)


@pytest.fixture
def page(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    host = SettingsHost()
    qml = tmp_path / "host.qml"
    qml.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'SetupPage { width: 800; height: 600; settings: host\n'
        '  property var heard: []\n'
        '  onSwitchTheme: heard = heard.concat(["theme"])\n'
        '  onSwitchLanguage: heard = heard.concat(["language"])\n'
        '  onFlipBack: heard = heard.concat(["back"])\n'
        '  onToggleProjectsRow: heard = heard.concat(["projectsRow"])\n'
        '  onToggleTemplatesRow: heard = heard.concat(["templatesRow"])\n'
        '}\n', encoding="utf-8")
    view = QQuickView()
    view.rootContext().setContextProperty("host", host)
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(50)
    yield view, host
    view.close()


def _click(view, item):
    centre = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, centre.toPoint())
    QTest.qWait(30)


def _heard(view):
    heard = view.rootObject().property("heard")
    return heard.toVariant() if hasattr(heard, "toVariant") else heard


def test_four_tabs(page):
    view, _ = page
    assert [_named(view, f"tab{name}") is not None for name in ("General", "Scope", "Headline", "SunTree")] == [True] * 4


def test_general_switches_and_flipping_back(page):
    view, _ = page
    _click(view, _named(view, "setupTheme"))
    _click(view, _named(view, "setupLanguage"))
    _click(view, _named(view, "setupFlipBack"))
    assert _heard(view) == ["theme", "language", "back"]


def test_suntree_values_go_to_the_settings_file(page):
    from core.settings import Settings

    view, host = page
    _click(view, _named(view, "tabSunTree"))
    slider = _named(view, "setting_SunTree/enter")
    assert slider is not None and slider.property("value") == 0.75
    slider.setProperty("value", 0.85)
    QTest.qWait(30)
    assert Settings().get("SunTree/enter") == 0.85  # in the file, for SunTree to read

    _click(view, _named(view, "reset_SunTree/enter"))
    assert Settings().get("SunTree/enter") == 0.75 and slider.property("value") == 0.75


def test_the_small_crown_follows_the_sliders(page):
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    preview = _named(view, "crownPreview")
    assert preview is not None and preview.property("enter") == 0.75
    _named(view, "setting_SunTree/enter").setProperty("value", 0.9)
    QTest.qWait(30)
    assert abs(preview.property("enter") - 0.9) < 1e-9


ORDER = ["SunTree/inner", "SunTree/leave", "SunTree/lineT", "SunTree/enter",
         "SunTree/lens", "SunTree/softness", "SunTree/edge"]


def test_the_sliders_go_from_the_inside_out_each_explained(page):
    # In the order their lines lie in the small crown, then the three that are no line; a
    # line under each says what it does (the user does not know "crown" or "drawing in").
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    sliders = [_named(view, "setting_" + key) for key in ORDER]
    ys = [s.mapToScene(QPointF(0, 0)).y() for s in sliders]
    assert ys == sorted(ys)
    for key in ORDER:
        help_line = _named(view, "help_" + key)
        assert help_line is not None and help_line.isVisible() and len(help_line.property("text")) > 20


def test_over_a_slider_its_demo_plays_and_a_click_stops_it(page):
    from PySide6.QtCore import QPoint
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    preview = _named(view, "crownPreview")
    label = _named(view, "row_SunTree/lens")
    at = label.mapToScene(QPointF(label.width() / 2, label.height() / 2)).toPoint()
    QTest.mouseMove(view, at)
    QTest.qWait(100)
    assert preview.property("demo") == "lens"
    slider = _named(view, "setting_SunTree/lens")
    press = slider.mapToScene(QPointF(slider.width() / 2, slider.height() / 2)).toPoint()
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, press)
    QTest.qWait(50)
    assert preview.property("demo") == ""  # following the slider now
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, press)
    QTest.qWait(50)
    assert preview.property("demo") == ""  # and stays quiet while the mouse is on the row
    QTest.mouseMove(view, QPoint(5, 5))  # away ...
    QTest.qWait(50)
    QTest.mouseMove(view, at)  # ... and back: it shows again
    QTest.qWait(100)
    assert preview.property("demo") == "lens"


def test_the_scope_tab_switches_the_two_rows(page):
    view, _ = page
    _click(view, _named(view, "tabScope"))
    _click(view, _named(view, "checkProjectsRow"))
    _click(view, _named(view, "checkTemplatesRow"))
    assert _heard(view)[-2:] == ["projectsRow", "templatesRow"]


def test_done_stands_top_left(page):
    view, _ = page
    done = _named(view, "setupFlipBack").mapToScene(QPointF(0, 0))
    title = _named(view, "setupTitle").mapToScene(QPointF(0, 0))
    assert done.x() < title.x() and abs(done.y() - title.y()) < 20


def test_suggested_myos_folders_pale_with_a_live_preview_in_all_three_styles(page):
    # For the user embryos are "suggested MyOS folders". The preview shows a present one beside
    # a suggestion in each style, drawn as Scope's rows draw them: the fill and frame pale, the
    # badge as pale as its own slider says, the name full.
    from PySide6.QtGui import QColor

    view, _ = page
    slider = _named(view, "setting_General/embryoOpacity")
    badges = _named(view, "setting_General/embryoBadgeOpacity")
    styles = ("text", "smallIcon", "largeIcon")
    suggestions = [_named(view, "suggestionPreview_" + style) for style in styles]
    present = [_named(view, "presentPreview_" + style) for style in styles]
    assert slider is not None and badges is not None and all(suggestions) and all(present)
    assert [s.property("style") for s in suggestions] == list(styles)

    def fill_alpha(item):
        return QColor(item.property("fillColor")).alphaF()

    assert all(abs(fill_alpha(s) - 0.4) < 0.01 for s in suggestions)
    assert all(abs(s.property("badgeOpacity") - 0.7) < 1e-6 for s in suggestions)
    assert all(fill_alpha(p) > 0.99 and p.property("badgeOpacity") == 1.0 for p in present)
    slider.setProperty("value", 0.6)
    badges.setProperty("value", 0.9)
    QTest.qWait(30)
    assert all(abs(fill_alpha(s) - 0.6) < 0.01 and abs(s.property("badgeOpacity") - 0.9) < 1e-6 for s in suggestions)
    root = view.rootObject()
    assert abs(root.property("embryoOpacity") - 0.6) < 1e-6 and abs(root.property("embryoBadgeOpacity") - 0.9) < 1e-6


def test_suggestion_left_present_right_sliders_beside(page):
    view, _ = page
    for style in ("text", "smallIcon", "largeIcon"):
        suggestion = _named(view, "suggestionPreview_" + style).mapToScene(QPointF(0, 0))
        present = _named(view, "presentPreview_" + style).mapToScene(QPointF(0, 0))
        assert suggestion.x() < present.x()
    right_of_examples = _named(view, "presentPreview_largeIcon").mapToScene(QPointF(130, 0)).x()
    for key in ("General/embryoOpacity", "General/embryoBadgeOpacity"):
        assert _named(view, "setting_" + key).mapToScene(QPointF(0, 0)).x() > right_of_examples


def _left_of(view, example, control):
    return _named(view, example).mapToScene(QPointF(_named(view, example).width(), 0)).x() <= \
        _named(view, control).mapToScene(QPointF(0, 0)).x()


def test_the_rows_one_example_left_check_items_right(page):
    # One example, as the rows really look (the path segments pushed together like tabs), shows
    # what the check items on the right set; each check item is kept for both rows.
    from core.settings import Settings

    view, _ = page
    root = view.rootObject()
    _click(view, _named(view, "tabScope"))
    example = _named(view, "rowsExample")
    for name, key, start, shows in (("PathBar", "Scope/pathBar", True, "pathBar"),
                                    ("Preview", "Scope/preview", True, "preview"),
                                    ("PreviewBackground", "Scope/previewBackground", False, "previewBackground"),
                                    ("Suggestions", "Scope/showSuggestions", True, "suggestions"),
                                    ("Hidden", "Scope/showHidden", False, "hidden")):
        check = _named(view, "check" + name)
        assert _left_of(view, "rowsExample", "check" + name)
        assert check.property("checked") is start and example.property(shows) is start
        _click(view, check)
        assert check.property("checked") is (not start) and example.property(shows) is (not start)
        assert Settings().get(key) is (not start)
    assert root.property("pathBarOn") is False and root.property("previewBackgroundOn") is True


def test_the_styles_of_both_rows(page):
    from core.settings import Settings

    view, _ = page
    _click(view, _named(view, "tabScope"))
    example = _named(view, "rowsExample")
    assert example.property("folderStyle") == "smallIcon"
    _click(view, _named(view, "templatesStyle_largeIcon"))
    assert example.property("folderStyle") == "largeIcon" and Settings().get("Scope/templatesStyle") == "largeIcon"
    _click(view, _named(view, "projectsStyle_smallIcon"))
    assert view.rootObject().property("projectsStyle") == "smallIcon" and Settings().get("Scope/projectsStyle") == "smallIcon"


def test_rows_and_preview_behaviour(page):
    from core.settings import Settings

    view, _ = page
    root = view.rootObject()
    _click(view, _named(view, "tabScope"))
    assert root.property("projectsRowShown") is False  # the projects row off by default
    _click(view, _named(view, "checkInstantReopen"))
    assert Settings().get("Scope/instantReopen") is False and root.property("instantReopenOn") is False
    _click(view, _named(view, "tuning_soft"))
    assert Settings().get("Scope/previewTuning") == "soft"
    timing = root.property("previewTiming")
    timing = timing.toVariant() if hasattr(timing, "toVariant") else timing
    assert timing["hoverDelayMs"] == 110


def test_the_sliders_keep_room_beside_the_examples(page):
    view, _ = page  # 800 px wide
    for key in ("General/embryoOpacity", "General/embryoBadgeOpacity"):
        assert _named(view, "setting_" + key).width() >= 120


def test_nothing_runs_off_the_right_edge(page):
    view, _ = page  # 800 px wide
    for key in ("General/embryoOpacity", "General/embryoBadgeOpacity"):
        reset = _named(view, "reset_" + key)
        assert reset.mapToScene(QPointF(reset.width(), 0)).x() <= view.width()


def _scene(view, name, x=0, y=0):
    return _named(view, name).mapToScene(QPointF(x, y))


def test_display_on_top_myos_folders_above_projects_with_their_styles(page):
    # "Display": per row its check item, right of it the row's three folder styles; the MyOS
    # folders first, as their row is the upper one. Then what both rows show.
    view, _ = page
    _click(view, _named(view, "tabScope"))
    templates, projects = _scene(view, "checkTemplatesRow"), _scene(view, "checkProjectsRow")
    assert templates.y() < projects.y() < _scene(view, "checkPathBar").y()
    for check, prefix in (("checkTemplatesRow", "templatesStyle"), ("checkProjectsRow", "projectsStyle")):
        row = _scene(view, check, 0, _named(view, check).height() / 2)
        for style in ("text", "smallIcon", "largeIcon"):
            button = _scene(view, prefix + "_" + style, 0, _named(view, prefix + "_" + style).height() / 2)
            assert button.x() > row.x() + _named(view, check).width() and abs(button.y() - row.y()) < 4


def test_the_example_keeps_one_line_per_row_and_its_rows_touch(page):
    view, _ = page
    _click(view, _named(view, "tabScope"))
    for name in ("checkHidden",):  # path bar is on: path bar, folders with the hidden one
        _click(view, _named(view, name))
    for style in ("text", "smallIcon", "largeIcon"):
        _click(view, _named(view, "templatesStyle_" + style))
        folders = [i for i in _walk(_named(view, "rowsExample")) if i.objectName().startswith("exampleFolder_")]
        segments = [i for i in _walk(_named(view, "rowsExample")) if i.objectName().startswith("exampleSegment_")]
        assert len({round(f.mapToScene(QPointF(0, 0)).y()) for f in folders if f.isVisible()}) == 1, style
        lowest_segment = max(s.mapToScene(QPointF(0, s.height())).y() for s in segments)
        top_folder = min(f.mapToScene(QPointF(0, 0)).y() for f in folders if f.isVisible())
        assert top_folder <= lowest_segment, style  # touching, even overlapping


def test_the_scope_tab_fits_the_width(page):
    view, _ = page  # 800 px wide
    _click(view, _named(view, "tabScope"))
    for name in ("templatesStyle_largeIcon", "projectsStyle_largeIcon"):
        button = _named(view, name)
        assert button.mapToScene(QPointF(button.width(), 0)).x() <= view.width() - 16, name


def test_without_the_path_bar_the_example_shows_up(page):
    view, _ = page
    _click(view, _named(view, "tabScope"))
    assert not _named(view, "exampleUp").isVisible()
    _click(view, _named(view, "checkPathBar"))
    up = _named(view, "exampleUp")
    assert up.isVisible() and up.mapToScene(QPointF(up.width(), 0)).x() <= _scene(view, "exampleSegment_0").x()
