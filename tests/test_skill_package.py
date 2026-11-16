"""Validate the Agensi skill package without changing MCP server behavior."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skill" / "gdsfactory-photonic-layout"
PACKAGE_SCRIPT = SKILL_ROOT / "scripts" / "package_skill.py"

# Import packaging helpers directly from the skill script.
import importlib.util

spec = importlib.util.spec_from_file_location("package_skill", PACKAGE_SCRIPT)
assert spec is not None and spec.loader is not None
package_skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_skill)


def test_required_skill_files_exist() -> None:
    for relative in package_skill.REQUIRED_RELATIVE_PATHS:
        path = SKILL_ROOT / relative
        assert path.is_file(), f"missing {relative}"
        assert path.stat().st_size > 0


def test_skill_frontmatter() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    meta = package_skill.parse_frontmatter(text)
    assert meta["name"] == "gdsfactory-photonic-layout"
    assert "use when" in meta["description"].lower()
    assert "do not use" in meta["description"].lower()


def test_listing_files_are_english() -> None:
    chinese = re.compile(r"[\u4e00-\u9fff]")
    for relative in package_skill.REQUIRED_RELATIVE_PATHS:
        content = (SKILL_ROOT / relative).read_text(encoding="utf-8")
        assert not chinese.search(content), f"Chinese found in {relative}"


def test_package_zip_structure(tmp_path: Path) -> None:
    output = tmp_path / "gdsfactory-photonic-layout.zip"
    package_skill.build_zip(SKILL_ROOT, output)
    assert output.is_file()
    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
    assert "gdsfactory-photonic-layout/SKILL.md" in names
    tops = {name.split("/", 1)[0] for name in names}
    assert tops == {"gdsfactory-photonic-layout"}
    assert not any("__MACOSX" in name or name.endswith(".DS_Store") for name in names)


def test_validate_skill_clean() -> None:
    assert package_skill.validate_skill(SKILL_ROOT) == []
