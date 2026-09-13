# 研究依据与本 skill 的设计决策

资料核对日期：2026-09-13。以下内容均为官方资料的提炼与本 skill 的工程化推论，不复制长段原文。模型名称、上限、价格与弃用日期会变化；执行时如需精确型号信息，应重新查官方文档。

## Google Gemini / Nano Banana

### Nano Banana image generation

来源：https://ai.google.dev/gemini-api/docs/image-generation

官方资料表明：Gemini 原生图像能力支持文本+图像编辑、局部添加/移除/修改、颜色分级、多轮编辑、多参考图、输出比例与尺寸控制；官方示例强调“只改指定对象、其余元素和光线保持不变”，并建议对需要保真的人物/标识具体描述关键特征。

落实到本 skill：

- 加入 `executor_profile`，区分显式蒙版与自然语言语义蒙版，不把提示词锁定误写成物理保证。
- 参考图按身份、服装、道具、色彩、构图和文字分工，避免无关内容串入。
- 高风险复合任务使用 `ordered_micro_passes`；失败只重试局部，而不是整图重跑。
- 加入 `text_plan`，但能力未知或必须零错字时回退为留白+宿主排字。
- 不在固定 skill 中写死某一型号和能力上限；型号信息属于易变资料。

### Prompt design strategies

来源：https://ai.google.dev/gemini-api/docs/prompting-strategies

官方建议清晰、具体地给出指令和约束；复杂任务可拆步骤；少量示例能约束输出格式，但过多示例可能造成过拟合；复杂 JSON 更适合结构化输出或事后校验。

落实到本 skill：

- 把冗长、重复的锁定句压缩为一次全局合同，模块仅引用关键保留项。
- 使用五段式结构和固定键序，让“目标、区域、融入、验收”均可定位。
- 新增确定性 `validate_preset.py`，检查外层 JSON、内层 `content`、必需键、模块键和滑块 target。

### 官方图像提示最佳实践

来源同上：https://ai.google.dev/gemini-api/docs/image-generation

官方建议具体描述、补充用途与语境、复杂场景分步、迭代微调、使用摄影/电影语言控制相机，并用“语义负向”描述目标终态，而不只堆叠否定词。

落实到本 skill：

- `negative_prompt` 限于本次主要风险；先以正向句写期望终态。
- 特效条目强制相机空间信息：锚点、尺度、透视、遮挡、景深、颗粒与光照交互。
- 引入复杂度预算和最小遮罩重试策略。

## Adobe 官方资料

### Photoshop Generative Fill

来源：https://helpx.adobe.com/photoshop/desktop/create-open-import-images/create-images/edit-images-with-generative-fill.html

Adobe 的工作流先选择要变换的区域，再输入描述；空提示可依据周围像素补全，并从多个变化中选取。

落实到本 skill：

- 每个模块必须有 `authorized_area`，清理/补洞写邻域材质连续性。
- 对有显式蒙版能力的宿主，将 `lock_reliability` 标为 `strong`；对整图自然语言编辑只标 `best_effort`。
- 建议生成少量候选选优，但不以多次生成代替物理融入和验收。

### Adobe Firefly effective prompts

来源：https://helpx.adobe.com/uk/firefly/web/work-with-images/generate-images/writing-effective-text-prompts.html

Adobe 建议使用简单、直接、具体的主体与描述词，并通过改写迭代接近目标。

落实到本 skill：

- 删除无效形容词堆砌；每个形容词必须对应可见材质、光、空间或风格属性。
- 把“高级、大片、质感”转译为可观察的影调、高光滚降、材质粗糙度、景深和颗粒。

### Adobe Dimension Generative Background

来源：https://helpx.adobe.com/dimension/desktop/features/generative-background.html

Adobe 强调合成背景时要描述环境对象、材料、照明与透视，并通过匹配图像对齐相机和光线。

落实到本 skill：

- 新增内容必须匹配地平线/灭点、尺度、主光和投影；`integration` 不能只写“自然融合”。
- 大面积环境生成仍转半合成或大合成 skill，避免本 skill 越界。

## 资料使用原则

- 官方资料只提供能力与方法边界；COS 术语库是本 skill 自有的任务结构化总结。
- 不把营销措辞当作成功保证，不声称自然语言可以绝对锁像素。
- 任何当前型号、分辨率、参考图数量或弃用信息，回答用户时必须重新联网核对。

## 2026-09-13 第二轮功能扩展

### Photoshop Harmonize

来源：https://helpx.adobe.com/photoshop/desktop/repair-retouch/remove-objects-fill-space/blend-subjects-with-harmonize.html

Adobe 将新增主体与背景的颜色、照明、阴影和色调匹配视为独立合成步骤。落实为 `subject_harmonize_plan`：只调整新增主体及其接触/边缘区，底图是基准，不通过全图调色掩盖拼接。

### Photoshop Reflection Removal

来源：https://helpx.adobe.com/photoshop/desktop/repair-retouch/clean-restore-images/remove-reflections.html

Adobe 的反光移除面向隔窗拍摄产生的大面积反射，并支持保留清理层、反射层和原始层。落实为 `glass_reflection_fix`：区分反射与透过玻璃的真实内容，保留可逆/分层思路，避免把主体误删。

### Photoshop General Distractions

来源：https://helpx.adobe.com/photoshop/desktop/repair-retouch/remove-objects-fill-space/review-and-refine-general-distractions.html

Adobe 允许分类选择干扰物并增删检测遮罩。落实为清理模块的目标分类与逐项授权：人物、器材、线缆、垃圾、反光等不能用一个笼统全图清理指令处理。

### Lightroom Generative Upscale 与 AI Sharpen

来源：https://helpx.adobe.com/lightroom/desktop/edit-photos/enhance-images-with-generative-ai.html

Adobe 把提高分辨率、细节增强和去模糊拆成可独立控制的任务。落实为 `low_light_rescue`、`capture_artifact_fix` 和 `material_texture_enhance_plan` 的分步顺序：先去伪影/噪声，再恢复已有细节，最后按材质微锐化。

### Photoshop Auto-Blend Layers

来源：https://helpx.adobe.com/photoshop/desktop/create-masks/blend-images/auto-blend-layers-command-overview.html

Adobe 的自动溶图通过图层蒙版平滑组合不同曝光、照明或焦点区域。落实为 `image_blend_plan`：先对齐，逐供体建立迁移白名单和蒙版，再做色光影协调与接缝检查；“溶图”不误解成随机像素的 Dissolve 模式。

### Gemini 多图组合

来源：https://ai.google.dev/gemini-api/docs/image-generation

Gemini 官方提供多图组合和关键细节保持的提示模板，强调明确指出从每张图取什么以及新增内容如何匹配环境光影。落实为 `base_image/donor_images/transfer_only/do_not_transfer` 与 `reference_roles`，并加入供体泄漏验收。
