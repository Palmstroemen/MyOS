# MyOS Sort Profiles - Design Document (MVP)

## 1. Purpose

`Sort.md` defines persistent auto-sorting rules for project folders.
Rules are path-aware, inherited by project ancestry, and usable across Scope, CLI, and other tools.

## 2. Canonical Location

- Local project rule file: `/.MyOS/Sort.md`
- Optional template-local rule file: `<TemplateRoot>/.MyOS/Sort.md`
- Optional global fallback: `<MyOSRoot>/.MyOS/Sort.md`

Resolution order:
1) current project local  
2) nearest ancestor local  
3) template-local (if in template context)  
4) global fallback

## 3. Rule Schema

Each rule is represented by one `# Sort` block:

```md
# Sort
Root: /Pictures
Pattern: {{YYYY}}/{{MM}}/{{DD}}
DateSource: exif_created,frontmatter_date,fs_mtime
ApplyOn: both
Materialization: on_use
Conflict: rename
Enabled: true
```

## 4. Token Whitelist

Allowed tokens:
- `{{YYYY}}`
- `{{YY}}`
- `{{MM}}`
- `{{MMMM}}`
- `{{DD}}`
- `{{ABC}}`

No other tokens are valid in MVP.

## 5. Validation Rules

- One date-tree anchor per branch:
  - duplicate date tokens in one pattern branch are invalid (example: `{{YYYY}}/.../{{YYYY}}`)
- Mixed type structure is valid:
  - `{{YYYY}}/.../{{MM}}/.../{{ABC}}`
- Recursive/unsafe path fragments are rejected:
  - `..`, absolute traversal fragments, or invalid separators
- Very deep dynamic trees are warned, not hard-failed.

## 6. Runtime Behavior

- If a file is dropped directly in configured `Root`, runtime computes `Pattern` and moves file.
- Conflict handling:
  - `rename` (default), `skip`, `error`
- Materialization:
  - `on_use` creates directories only when needed.

## 7. Safety

- Sorting never executes file content.
- Path traversal is rejected.
- Self-move loops are suppressed by runtime loop guard.
