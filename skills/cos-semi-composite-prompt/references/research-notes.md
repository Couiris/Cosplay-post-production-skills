# 研究依据与设计决策

资料核对日期：2026-09-14。本文件记录维护依据，不替代实际执行合同。

- [OpenAI 模型提示指南](https://developers.openai.com/api/docs/guides/latest-model) 强调清晰的指令层级、具体约束与可验证输出。落实为 `intent_card`、固定字段顺序、能力门、五道质量门和失败诊断。
- [OpenAI Skills API](https://developers.openai.com/api/reference/resources/skills) 将 skill 作为可复用、可版本化的资源。落实为薄入口 `SKILL.md`、按需读取的 `references/`、确定性验证脚本和前向评测样例。
- [Gemini 图像生成与编辑](https://ai.google.dev/gemini-api/docs/image-generation) 支持图像编辑、多轮编辑及多图组合，但具体能力会随模型变化。落实为 `executor_profile`、`reference_roles` 和 `runtime_bindings`；能力不足时不伪造可执行双阶段预设。
- [Adobe Photoshop 生成式 AI 概览](https://helpx.adobe.com/photoshop/desktop/generative-ai/generative-ai-features-overview.html) 将生成式添加、移除、扩展和协调视为可分离工作流。落实为显式 mask、补丁/透明层、不可变底图及宿主确定性装配，避免接受模型整图漂移。

这些来源只支持通用工作流设计；字段名、阈值、阶段划分和 COS 约束是本 skill 的工程约定，不宣称为模型厂商原生 schema。
