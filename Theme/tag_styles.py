"""Shared tag chip styles for MyOS apps."""

from __future__ import annotations


def build_tag_chip_styles(chip_bg: str, chip_fg: str) -> str:
    """Return stylesheet for a rounded tag/color chip button."""
    return f"""
                QPushButton {{
                    background-color: {chip_bg};
                    color: {chip_fg};
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

