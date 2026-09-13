from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = (
    "cos-basic-vfx-prompt",
    "cos-semi-composite-prompt",
    "cos-large-composite-prompt",
)
COMMUNITY_FILES = (
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def frontmatter(text: str) -> tuple[str | None, str | None]:
    if not text.startswith("---\n"):
        return None, None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, None
    header = text[4:end]
    name_match = re.search(r"(?m)^name:\s*([^\n]+)$", header)
    description_match = re.search(r"(?m)^description:\s*(.*)$", header)
    return (
        name_match.group(1).strip().strip('"\'') if name_match else None,
        description_match.group(1).strip() if description_match else None,
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    errors: list[str] = []
    manifest_path = ROOT / "skills-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"manifest 无法读取：{exc}")
        manifest = {}

    manifest_names = [item.get("name") for item in manifest.get("skills", [])]
    if manifest_names != list(EXPECTED):
        errors.append("skills-manifest.json 中的 skill 顺序或名称不正确")
    if manifest.get("author") != "Couiris":
        errors.append("skills-manifest.json 作者不是 Couiris")
    if manifest.get("license") != "MIT":
        errors.append("skills-manifest.json 许可证不是 MIT")

    for relative_path in COMMUNITY_FILES:
        if not (ROOT / relative_path).is_file():
            errors.append(f"缺少开源社区文件：{relative_path}")

    for skill_name in EXPECTED:
        skill_root = ROOT / "skills" / skill_name
        entry = skill_root / "SKILL.md"
        agent = skill_root / "agents" / "openai.yaml"
        if not entry.is_file():
            errors.append(f"{skill_name}: 缺少 SKILL.md")
            continue
        if not agent.is_file():
            errors.append(f"{skill_name}: 缺少 agents/openai.yaml")

        text = entry.read_text(encoding="utf-8")
        name, description = frontmatter(text)
        if name != skill_name:
            errors.append(f"{skill_name}: frontmatter name 为 {name!r}")
        if description is None:
            errors.append(f"{skill_name}: 缺少 description")
        if "TODO" in text or "PLACEHOLDER" in text:
            errors.append(f"{skill_name}: 仍有未完成占位内容")

        if agent.is_file():
            agent_text = agent.read_text(encoding="utf-8")
            for required_field in (
                "interface:",
                "display_name:",
                "short_description:",
                "default_prompt:",
            ):
                if required_field not in agent_text:
                    errors.append(f"{skill_name}: agents/openai.yaml 缺少 {required_field}")

        for markdown in skill_root.rglob("*.md"):
            markdown_text = markdown.read_text(encoding="utf-8")
            for target in LINK_RE.findall(markdown_text):
                clean_target = target.split("#", 1)[0]
                if not clean_target or "://" in clean_target or clean_target.startswith("mailto:"):
                    continue
                resolved = (markdown.parent / clean_target).resolve()
                if not resolved.exists():
                    errors.append(f"{markdown.relative_to(ROOT)}: 无效链接 {target}")

        for json_file in skill_root.rglob("*.json"):
            try:
                json.loads(json_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{json_file.relative_to(ROOT)}: JSON 无效（{exc}）")

    forbidden = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.name == "__pycache__" or path.suffix == ".pyc"
    ]
    if forbidden:
        errors.append("仓库包含缓存文件：" + ", ".join(map(str, forbidden)))

    if errors:
        print(f"校验失败：{len(errors)} 个问题")
        for error in errors:
            print(f"- {error}")
        return 1

    file_count = sum(1 for path in ROOT.rglob("*") if path.is_file())
    print(f"校验通过：{len(EXPECTED)} 个 skills，{file_count} 个文件，结构、链接和 JSON 均有效")
    return 0


if __name__ == "__main__":
    sys.exit(main())
