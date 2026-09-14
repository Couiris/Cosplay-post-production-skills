#!/usr/bin/env python3
"""Audit two-stage composite skill documentation and regression assets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    mode = "semi" if "semi" in root.name else "large"
    errors: list[str] = []
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if not re.match(r"^---\n.*?\n---\n", skill, re.DOTALL):
        errors.append("SKILL.md frontmatter format invalid")
    for required in (
        "references/request-routing-qc.md", "references/output-schema.md",
        "scripts/validate_pair.py", "scripts/test_validator.py", "scripts/audit_skill.py",
    ):
        if required not in skill:
            errors.append(f"SKILL.md missing required link or command: {required}")
    for path in (root / "scripts" / "validate_pair.py", root / "scripts" / "test_validator.py"):
        if not path.is_file():
            errors.append(f"missing script: {path.name}")

    eval_path = root / "evals" / "forward-cases.json"
    if not eval_path.is_file():
        errors.append("missing evals/forward-cases.json")
    else:
        try:
            eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
            if eval_data.get("skill_mode") != f"{mode}_composite":
                errors.append("forward eval skill_mode mismatch")
            if not isinstance(eval_data.get("cases"), list) or len(eval_data["cases"]) < 3:
                errors.append("forward eval suite must contain at least 3 cases")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid forward eval suite: {exc}")

    routing = (root / "references" / "request-routing-qc.md").read_text(encoding="utf-8")
    schema = (root / "references" / "output-schema.md").read_text(encoding="utf-8")
    terms = (
        "intent_card", "executor_profile", "pair_manifest", "runtime_bindings",
        "subject_relight_overlay_rgba", "foreground_occluder_rgba", "五道质量门",
    )
    for term in terms:
        if term not in routing and term not in schema:
            errors.append(f"missing contract term: {term}")
    if mode == "semi":
        for term in ("visible_retained_scene_lock", "occluded_reconstruction_mask", "original_to_final_translation_px"):
            if term not in routing and term not in schema:
                errors.append(f"missing semi contract term: {term}")
    else:
        for term in ("subjects[]", "shadow_mode", "vfx_stage_assignment", "composition_budget"):
            if term not in routing and term not in schema:
                errors.append(f"missing large contract term: {term}")

    for json_path in (root / "references").glob("*.json"):
        try:
            json.loads(json_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {json_path.name}: {exc}")

    link_pattern = re.compile(r"\]\(([^)]+)\)")
    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for link in link_pattern.findall(text):
            if link.startswith(("http://", "https://", "#", "$")):
                continue
            relative = link.split("#", 1)[0]
            if relative and not (markdown.parent / relative).exists():
                errors.append(f"broken link in {markdown.relative_to(root)}: {link}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"审计失败：{len(errors)} 个错误")
        return 1
    print(f"审计通过：{mode} 两阶段合同、脚本、JSON 与文档链接有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
