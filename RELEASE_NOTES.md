# Release notes — v2.0.0 (2026-09-14)

Maintainer: Couiris

## Included skills

- `cos-basic-vfx-prompt`：61 个模块、90 项特效，增强质感、虚拟打光、多供体溶图、条件式边缘/成像协调及单预设校验。
- `cos-semi-composite-prompt`：加入能力门、双阶段配对 manifest、多人锁定、可见原景与遮挡补洞分离、最终人物染光/前景装配层及双预设校验。
- `cos-large-composite-prompt`：加入多人/悬浮人物分支、VFX 阶段分配、构图预算、无人无影底板、最终人物染光/前景装配层及双预设校验。

## Repository readiness

- MIT License；
- README、贡献指南、行为准则和安全政策；
- Bug、功能建议和 Pull Request 模板；
- 三技能统一清单、前向评测用例与仓库级结构、链接、JSON、回归测试校验器；
- GitHub Actions 在 push 与 pull request 时自动验证；
- 发布包排除 `__pycache__`、`.pyc`、日志和编辑器配置。

此版本统一了三套 skill 的提示词架构、能力边界、分层输出、质量门和失败策略。两阶段 schema 有显著增强，旧预设应重新生成并用新版校验器检查。
