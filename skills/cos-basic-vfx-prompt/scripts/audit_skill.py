#!/usr/bin/env python3
"""Audit registry, effect numbering, links, and bundled preset templates."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from validate_preset import MODULES, validate


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    if not re.match(r"^---\n.*?\n---\n", skill_text, re.DOTALL):
        errors.append("SKILL.md frontmatter format invalid")
    if re.search(r"(?m)^\s*\[TODO:", skill_text):
        errors.append("SKILL.md contains unfinished TODO")

    registry_text = (root / "references" / "module-registry.md").read_text(encoding="utf-8")
    registry_modules = set(re.findall(r"^\| `([a-z0-9_]+)` \|", registry_text, re.MULTILINE))
    if registry_modules != MODULES:
        missing_in_validator = sorted(registry_modules - MODULES)
        missing_in_registry = sorted(MODULES - registry_modules)
        errors.append(
            "module registry mismatch: "
            f"missing_in_validator={missing_in_validator}, missing_in_registry={missing_in_registry}"
        )
    count_match = re.search(r"共 (\d+) 个规范模块", registry_text)
    if not count_match or int(count_match.group(1)) != len(registry_modules):
        errors.append("declared module count does not match registry table")

    effects_text = (root / "references" / "effects-library.md").read_text(encoding="utf-8")
    effect_numbers = [int(value) for value in re.findall(r"^## (\d+)\.", effects_text, re.MULTILINE)]
    if effect_numbers != list(range(1, 91)):
        errors.append("effect headings must be a complete 1..90 sequence")
    if "选效与组合速查（90 项）" not in effects_text:
        errors.append("effect summary count is not 90")

    link_pattern = re.compile(r"\]\(([^)]+)\)")
    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for link in link_pattern.findall(text):
            if link.startswith(("http://", "https://", "#", "$")):
                continue
            relative = link.split("#", 1)[0]
            if relative and not (markdown.parent / relative).exists():
                errors.append(f"broken link in {markdown.relative_to(root)}: {link}")

    templates = sorted((root / "references").glob("*template.json"))
    if len(templates) < 2:
        errors.append("expected at least the base and lighting/blending templates")
    for template in templates:
        preset_errors, _ = validate(template)
        if preset_errors:
            errors.append(f"{template.name}: {'; '.join(preset_errors)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"审计失败：{len(errors)} 个错误")
        return 1

    print(
        f"审计通过：{len(registry_modules)} 个模块，{len(effect_numbers)} 项特效，"
        f"{len(templates)} 个模板，文档链接有效"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
