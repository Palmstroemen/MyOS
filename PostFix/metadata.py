"""Metadata helpers for PostFix markdown documents."""

import yaml

FRONTMATTER_BOUNDARY = "---"


class MetadataManager:
    """Handle YAML frontmatter parsing and updates for markdown text."""

    def split_frontmatter(self, text: str):
        lines = text.splitlines()
        if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
            return {}, text
        for idx in range(1, len(lines)):
            if lines[idx].strip() == FRONTMATTER_BOUNDARY:
                yaml_text = "\n".join(lines[1:idx]).strip()
                body = "\n".join(lines[idx + 1 :]).lstrip("\n")
                data = yaml.safe_load(yaml_text) if yaml_text else {}
                return data or {}, body
        return {}, text

    def build_frontmatter(self, meta: dict, body: str) -> str:
        yaml_text = yaml.safe_dump(meta, sort_keys=False).strip()
        if yaml_text:
            return f"{FRONTMATTER_BOUNDARY}\n{yaml_text}\n{FRONTMATTER_BOUNDARY}\n{body.lstrip()}"
        return body

    def update_field(self, text: str, key: str, value) -> str:
        meta, body = self.split_frontmatter(text)
        meta[key] = value
        return self.build_frontmatter(meta, body)

    def get_field(self, text: str, key: str):
        meta, _ = self.split_frontmatter(text)
        return meta.get(key)
