"""Shared tag chip style helpers for MyOS applications."""

from __future__ import annotations


def build_tag_chip_stylesheet(background: str, foreground: str) -> str:
    """Return a consistent tag-chip stylesheet for QPushButton."""
    bg = str(background or "#ffd54f")
    fg = str(foreground or "#1f1f1f")
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: 1px solid rgba(0, 0, 0, 60);
            border-top-left-radius: 2px;
            border-bottom-left-radius: 2px;
            border-top-right-radius: 12px;
            border-bottom-right-radius: 12px;
            text-align: right;
            padding: 4px 8px;
            margin: 3px;
        }}
        QPushButton:hover {{
            border: 2px solid rgba(0, 0, 0, 95);
        }}
    """

