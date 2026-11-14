"""The back of Scope (Scope/SetupPage.qml; Scope/Designdocument Setup.md): tabs General, Scope,
Headline, SunTree; what is set there goes to the one settings file (core/settings.py)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

from core import color_schemes

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

    @Slot(str, result="QVariantMap")
    def colorScheme(self, name):
        return color_schemes.load_scheme(name)

    @Slot(str, str, str, result=bool)
    def setSchemeColor(self, name, color, value):
        return color_schemes.set_scheme_color(name, color, value)

    @Slot(str, str)
    def resetSchemeColor(self, name, color):
        color_schemes.reset_scheme_color(name, color)

    @Slot(str, str, result=str)
    def schemeColorDefault(self, name, color):
        return color_schemes.shipped_scheme(name)[color]

    @Slot(str)
    def resetSchemeColors(self, name):
        color_schemes.reset_scheme(name)

    @Slot(str, result=bool)
    def schemeHasOwnColors(self, name):
        return color_schemes.has_own_colors(name)


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
        '  onSchemeColorEdited: heard = heard.concat(["edited"])\n'
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
    _click(view, _named(view, "schemeCard_dark"))  # worn already: nothing to switch
    _click(view, _named(view, "schemeCard_light"))
    _click(view, _named(view, "setupLanguage"))
    _click(view, _named(view, "setupFlipBack"))
    assert _heard(view) == ["theme", "language", "back"]


def test_each_scheme_card_shows_its_own_colours(page):
    view, _ = page
    for name in ("dark", "light"):
        card = _named(view, f"schemeCard_{name}")
        assert card.property("selected") is (name == "dark")
        center = _named(view, f"schemeCenter_{name}")
        assert QColor(center.property("color")) == QColor(color_schemes.load_scheme(name)["filesPanelCenter"])


def _picker(view):
    return view.rootObject().findChild(QObject, "schemeColorDialog")


def _open_picker(view):
    _click(view, _named(view, "colorSwatch_filesPanelCenter"))
    QTest.qWait(30)
    picker = _picker(view)
    assert picker.property("visible") is True
    return picker


def test_a_click_on_the_little_box_opens_the_colour_picker_on_its_colour(page):
    view, _ = page
    assert _picker(view).property("visible") is False
    picker = _open_picker(view)
    assert picker.property("selectedColor") == QColor(color_schemes.load_scheme("dark")["filesPanelCenter"])
    QMetaObject.invokeMethod(picker, "reject")


def test_the_files_background_is_set_for_the_scheme_worn(page):
    view, _ = page
    light = color_schemes.load_scheme("light")["filesPanelCenter"]
    picker = _open_picker(view)
    picker.setProperty("selectedColor", QColor("#123456"))
    QTest.qWait(30)
    assert color_schemes.load_scheme("dark")["filesPanelCenter"] == "#123456"  # counts at once, the picker still open
    assert "edited" in _heard(view)
    assert QColor(_named(view, "schemeCenter_dark").property("color")) == QColor("#123456")  # the card follows
    assert QColor(_named(view, "colorSwatch_filesPanelCenter").property("color")) == QColor("#123456")
    QMetaObject.invokeMethod(picker, "accept")
    QTest.qWait(30)
    assert color_schemes.load_scheme("dark")["filesPanelCenter"] == "#123456"
    assert color_schemes.load_scheme("light")["filesPanelCenter"] == light  # the other scheme is left alone


def test_cancelling_the_picker_leaves_the_colour_as_it_was(page):
    view, _ = page
    before = color_schemes.load_scheme("dark")["filesPanelCenter"]
    picker = _open_picker(view)
    picker.setProperty("selectedColor", QColor("#123456"))
    QTest.qWait(30)
    QMetaObject.invokeMethod(picker, "reject")
    QTest.qWait(30)
    assert color_schemes.load_scheme("dark")["filesPanelCenter"] == before
    assert not color_schemes.own_colors_path("dark").exists() or "filesPanelCenter" not in color_schemes.own_colors_path("dark").read_text()


def test_the_little_box_follows_when_the_scheme_changes(page):
    view, _ = page
    swatch = _named(view, "colorSwatch_filesPanelCenter")
    assert QColor(swatch.property("color")) == QColor(color_schemes.load_scheme("dark")["filesPanelCenter"])
    view.rootObject().setProperty("darkTheme", False)
    QTest.qWait(30)
    assert QColor(swatch.property("color")) == QColor(color_schemes.load_scheme("light")["filesPanelCenter"])


def _drag_swatch(view, dx, dy=0):
    swatch = _named(view, "colorSwatch_filesPanelCenter")
    start = swatch.mapToScene(QPointF(swatch.width() / 2, swatch.height() / 2)).toPoint()
    QTest.mouseMove(view, start)
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, start)
    steps = 6
    for step in range(1, steps + 1):
        QTest.mouseMove(view, QPoint(start.x() + dx * step // steps, start.y() + dy * step // steps))
        QTest.qWait(10)
    return start


def _lightness(view):
    return QColor(_named(view, "colorSwatch_filesPanelCenter").property("color")).lightnessF()


@pytest.mark.parametrize("dx, lighter", [(120, True), (-120, False)])
def test_dragging_the_little_box_makes_the_colour_lighter_or_darker(page, dx, lighter):
    view, _ = page
    before = _lightness(view)
    swatch = _named(view, "colorSwatch_filesPanelCenter")
    position = swatch.position()
    start = _drag_swatch(view, dx)
    during = _lightness(view)  # shown at once, the mouse still down
    assert (during > before) is lighter and abs(during - before) > 0.1
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(start.x() + dx, start.y()))
    QTest.qWait(30)
    assert swatch.position() == position  # the box stays where it is
    assert _picker(view).property("visible") is False  # a drag opens no picker
    assert abs(QColor(color_schemes.load_scheme("dark")["filesPanelCenter"]).lightnessF() - during) < 0.01
    assert "edited" in _heard(view)


def test_dragging_keeps_the_hue_of_the_colour(page):
    view, _ = page
    color_schemes.set_scheme_color("dark", "filesPanelCenter", "#3060a0")
    view.rootObject().setProperty("schemeEdits", 1)
    hue = QColor("#3060a0").hslHueF()
    start = _drag_swatch(view, 60)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(start.x() + 60, start.y()))
    QTest.qWait(30)
    assert abs(QColor(color_schemes.load_scheme("dark")["filesPanelCenter"]).hslHueF() - hue) < 0.01


@pytest.mark.parametrize("dy, more", [(-60, True), (60, False)])
def test_dragging_up_makes_it_more_saturated_down_less(page, dy, more):
    view, _ = page
    color_schemes.set_scheme_color("dark", "filesPanelCenter", "#3060a0")
    view.rootObject().setProperty("schemeEdits", 1)
    start = _drag_swatch(view, 0, dy)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(start.x(), start.y() + dy))
    QTest.qWait(30)
    after = QColor(color_schemes.load_scheme("dark")["filesPanelCenter"])
    before = QColor("#3060a0")
    assert (after.hslSaturationF() > before.hslSaturationF()) is more
    assert abs(after.hslHueF() - before.hslHueF()) < 0.01 and abs(after.lightnessF() - before.lightnessF()) < 0.01
    assert _picker(view).property("visible") is False


def test_the_light_stops_at_white_and_black(page):
    view, _ = page
    start = _drag_swatch(view, 600)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(start.x() + 600, start.y()))
    QTest.qWait(30)
    assert color_schemes.load_scheme("dark")["filesPanelCenter"] == "#ffffff"


def test_a_shaky_click_still_opens_the_picker(page):
    view, _ = page
    before = color_schemes.load_scheme("dark")["filesPanelCenter"]
    start = _drag_swatch(view, 2)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(start.x() + 2, start.y()))
    QTest.qWait(30)
    assert _picker(view).property("visible") is True
    assert color_schemes.load_scheme("dark")["filesPanelCenter"] == before
    QMetaObject.invokeMethod(_picker(view), "reject")


ELEVEN = ["bg", "text", "filesPanelCenter", "panelAlt", "panel", "folderPathTint", "folderULineTint",
          "folderCwpTint", "fileSelectionFill", "dropHighlight", "lensFrame"]


def test_the_eleven_colours_have_their_little_boxes(page):
    view, _ = page
    swatches = [i.objectName() for i in _walk(view.rootObject()) if i.objectName().startswith("colorSwatch_")]
    assert sorted(swatches) == sorted(f"colorSwatch_{name}" for name in ELEVEN)
    for name in ELEVEN:
        shown = QColor(_named(view, f"colorSwatch_{name}").property("color"))
        assert shown == QColor(color_schemes.load_scheme("dark")[name]), name


def test_dragging_a_see_through_colour_keeps_it_see_through(page):
    view, _ = page
    before = QColor(color_schemes.load_scheme("dark")["fileSelectionFill"])
    assert before.alpha() < 255
    swatch = _named(view, "colorSwatch_fileSelectionFill")
    start = swatch.mapToScene(QPointF(swatch.width() / 2, swatch.height() / 2)).toPoint()
    QTest.mouseMove(view, start)
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, start)
    for step in range(1, 7):
        QTest.mouseMove(view, QPoint(start.x() + 10 * step, start.y()))
        QTest.qWait(10)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(start.x() + 60, start.y()))
    QTest.qWait(30)
    after = QColor(color_schemes.load_scheme("dark")["fileSelectionFill"])
    assert after.lightnessF() > before.lightnessF() and abs(after.alpha() - before.alpha()) <= 1


def test_the_picker_offers_opacity_only_for_see_through_colours(page):
    view, _ = page
    _click(view, _named(view, "colorSwatch_fileSelectionFill"))
    picker = _picker(view)
    assert picker.property("offersOpacity") is True
    QMetaObject.invokeMethod(picker, "reject")
    QTest.qWait(30)
    _click(view, _named(view, "colorSwatch_bg"))
    assert picker.property("offersOpacity") is False
    QMetaObject.invokeMethod(picker, "reject")


def test_all_colours_go_back_for_the_scheme_worn(page):
    view, _ = page
    reset_all = _named(view, "colorResetAll")
    assert reset_all.property("visible") is False  # nothing to go back from
    picker = _open_picker(view)
    picker.setProperty("selectedColor", QColor("#123456"))
    QMetaObject.invokeMethod(picker, "accept")
    QTest.qWait(30)
    color_schemes.set_scheme_color("light", "bg", "#654321")
    assert reset_all.property("visible") is True
    _click(view, reset_all)
    assert color_schemes.load_scheme("dark") == color_schemes.shipped_scheme("dark")
    assert color_schemes.load_scheme("light")["bg"] == "#654321"  # the other scheme keeps its own
    assert reset_all.property("visible") is False
    assert "edited" in _heard(view)


def test_no_way_back_beside_the_little_box(page):
    view, _ = page
    assert _named(view, "colorReset_filesPanelCenter") is None


def test_a_colour_takes_one_line_no_sliders():
    # There will be ten or more of them.
    source = (SCOPE_DIR / "SetupPage.qml").read_text(encoding="utf-8")
    colour_setting = source[source.index("component ColorSetting"):source.index("// A setting that is on or off")]
    assert "Slider" not in colour_setting and "TextField" not in colour_setting


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


def test_the_small_crown_wears_the_scheme(page):
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    preview = _named(view, "crownPreview")
    assert preview.property("schemeColors") == color_schemes.load_scheme("dark")
    view.rootObject().setProperty("darkTheme", False)
    QTest.qWait(30)
    assert preview.property("schemeColors") == color_schemes.load_scheme("light")


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


def test_suggested_settings_folders_pale_with_a_live_preview_in_all_three_styles(page):
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


def test_display_on_top_settings_folders_above_projects_with_their_styles(page):
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
