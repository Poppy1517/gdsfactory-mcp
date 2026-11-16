#!/usr/bin/env python3
"""Build dist/gdsfactory-photonic-layout.zip for Agensi upload.

Self-contained: discovers the skill folder from this script path, validates
required files, and writes a single top-level folder ZIP (no nested nesting,
no .DS_Store / __MACOSX / caches).
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

SKILL_NAME = "gdsfactory-photonic-layout"
REQUIRED_RELATIVE_PATHS = (
    "SKILL.md",
    "README.md",
    "references/mcp-tools.md",
    "references/components.md",
    "references/units-and-parameters.md",
    "references/workflow.md",
    "references/troubleshooting.md",
    "examples/straight-taper.md",
    "examples/bent-route.md",
    "examples/mmi-1x4-splitter.md",
    "listing/PRODUCT.md",
)
SKIP_DIR_NAMES = {".git", "__pycache__", ".venv", "node_modules"}
SKIP_FILE_NAMES = {".DS_Store", "Thumbs.db"}
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")
    data: dict[str, str] = {}
    key: str | None = None
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if key and (line.startswith("  ") or line.startswith("\t") or line.startswith("- ")):
            # Multi-line / list values: keep as opaque text for required-key checks.
            data[key] = f"{data[key]}\n{line}".strip()
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {raw_line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        data[key] = value.strip().strip("\"'")
    return data


def validate_skill(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_RELATIVE_PATHS:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"empty required file: {relative}")

    skill_md = root / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        try:
            meta = parse_frontmatter(text)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if meta.get("name") != SKILL_NAME:
                errors.append(
                    f"frontmatter name must be {SKILL_NAME!r}, got {meta.get('name')!r}"
                )
            description = meta.get("description", "")
            if len(description) < 40:
                errors.append("frontmatter description is too short")
            if "use when" not in description.lower():
                errors.append("frontmatter description should include 'Use when'")

        # Listing files must be English-facing prose (ASCII + common punctuation).
        for relative in REQUIRED_RELATIVE_PATHS:
            path = root / relative
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            if re.search(r"[\u4e00-\u9fff]", content):
                errors.append(f"Chinese characters found in listing file: {relative}")

    return errors


def iter_skill_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in SKIP_DIR_NAMES for part in relative_parts):
            continue
        if path.name in SKIP_FILE_NAMES:
            continue
        if path.suffix in {".pyc", ".pyo", ".so", ".dylib", ".exe", ".dll"}:
            continue
        files.append(path)
    return files


def build_zip(root: Path, output: Path) -> Path:
    errors = validate_skill(root)
    if errors:
        raise SystemExit("Skill validation failed:\n- " + "\n- ".join(errors))

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_skill_files(root):
            arcname = Path(SKILL_NAME) / path.relative_to(root)
            archive.write(path, arcname.as_posix())

    # Post-check: exactly one top-level folder, SKILL.md present.
    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
    if not any(name == f"{SKILL_NAME}/SKILL.md" for name in names):
        raise SystemExit("ZIP missing top-level SKILL.md")
    top_levels = {name.split("/", 1)[0] for name in names if name}
    if top_levels != {SKILL_NAME}:
        raise SystemExit(f"ZIP must contain only {SKILL_NAME}/, found {sorted(top_levels)}")

    return output


def main() -> int:
    root = skill_root()
    output = repo_root() / "dist" / f"{SKILL_NAME}.zip"
    path = build_zip(root, output)
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
