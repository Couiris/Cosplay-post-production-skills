# COS Composite Prompt Skills

一组面向 COS 场照与正片后期的 Codex skills，用于生成可导入 Nano Banana / Gemini 图像编辑插件的结构化 JSON 预设。

Post-production, VFX, relighting, multi-image blending, and staged compositing prompt skills for cosplay photography.

维护者：**Couiris**

## 如何选择

| Skill | 适用范围 | 不适用范围 |
| --- | --- | --- |
| `cos-basic-vfx-prompt` | 保留人物和大部分原场景；进行局部特效、清理修复、质感增强、虚拟打光、多图溶图、调色、有限扩图和成片包装 | 大面积重建场景 |
| `cos-semi-composite-prompt` | 保留场馆墙体、天花板和原机位；清场并增加地面、前中远景、浮空元素等半合成内容 | 完全替换为新世界 |
| `cos-large-composite-prompt` | 完全换景、扩画幅、海报级世界重构、巨型建筑/生物/载具和大量分层特效 | 只需小范围修图或轻特效 |

简单判断：原背景大部分保留用基础后期；保留场馆骨架但重铺场景用半合成；重建世界用大合成。

## 仓库结构

```text
skills/
├── cos-basic-vfx-prompt/
├── cos-semi-composite-prompt/
└── cos-large-composite-prompt/
scripts/
└── validate_skills.py
```

每个 skill 都是独立目录，包含入口 `SKILL.md`、界面元数据 `agents/openai.yaml`、按需加载的 `references/`、回归场景 `evals/` 与无第三方依赖的 `scripts/` 校验工具。

## 安装

将需要的整个 skill 目录复制到 Codex skills 目录中，保留目录名不变：

```powershell
Copy-Item -LiteralPath '.\skills\cos-basic-vfx-prompt' -Destination "$env:USERPROFILE\.codex\skills\cos-basic-vfx-prompt" -Recurse
Copy-Item -LiteralPath '.\skills\cos-semi-composite-prompt' -Destination "$env:USERPROFILE\.codex\skills\cos-semi-composite-prompt" -Recurse
Copy-Item -LiteralPath '.\skills\cos-large-composite-prompt' -Destination "$env:USERPROFILE\.codex\skills\cos-large-composite-prompt" -Recurse
```

安装后重新打开 Codex 会话，使技能列表重新加载。

## 校验

在仓库根目录运行：

```powershell
python scripts/validate_skills.py
```

根校验器会检查仓库结构、Markdown 链接、JSON、三个 skill 的审计与回归测试。生成具体预设后还可单独校验：

```powershell
python skills/cos-basic-vfx-prompt/scripts/validate_preset.py <preset.json>
python skills/cos-semi-composite-prompt/scripts/validate_pair.py <step1.json> <step2.json>
python skills/cos-large-composite-prompt/scripts/validate_pair.py <step1.json> <step2.json>
```

每次 push 与 pull request 也会通过 GitHub Actions 自动执行根校验器。

## 使用边界

- 生成式编辑对人物、姿态和背景的“锁定”取决于执行器是否支持蒙版、透明图层和确定性回贴；仅靠自然语言提示时属于 best effort。
- 半合成和大合成只有在人物抠图、显式 mask、透明 RGBA 补丁/图层、绝对坐标合成和像素差分能力可用时才标记为可执行。
- 参考图只应迁移用户明确指定的内容，不应带入无关人物、水印、签名、品牌或独特构图。
- 去水印功能只用于用户自有或已获授权的图片。
- 涉及人物服装覆盖修复时，不减少身体覆盖，不生成裸露内容。

## 参与贡献

提交问题或改进前请阅读 [贡献指南](CONTRIBUTING.md)、[行为准则](CODE_OF_CONDUCT.md) 和 [安全政策](SECURITY.md)。仓库提供了标准 Issue 表单和 Pull Request 模板。

## 许可证

Copyright © 2026 Couiris。项目使用 [MIT License](LICENSE)。
