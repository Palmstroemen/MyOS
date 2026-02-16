from Theme.tag_chips import build_tag_chip_stylesheet


def test_build_tag_chip_stylesheet_contains_colors_and_shape():
    css = build_tag_chip_stylesheet("#112233", "#f0f0f0")
    assert "background-color: #112233" in css
    assert "color: #f0f0f0" in css
    assert "border-top-right-radius: 12px" in css
    assert "text-align: right" in css

