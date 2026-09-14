# 提示词架构：少歧义、可局部重试

本文件定义预设的写法，不提供效果词库。目标是让执行器明确“改什么、保留什么、如何融入、怎样算成功”，同时控制提示词长度和冲突。

## 1. 内层总结构

推荐键序：

1. `role_instruction`
2. `task_summary`
3. `intent_card`（用户要求、保留项、禁改项、参考图职责、交付物和不确定项）
4. `photo_readout`
5. `executor_profile`
6. `execution_strategy`
7. `priority_order`
8. 三份锁定合同与 `subject_light_profile`
9. `reference_roles`（有参考图时）
10. `pass_plan`（仅复杂请求）
11. 启用模块
12. `authorization_contract`
13. `integration`
14. `acceptance_tests`
15. `retry_policy`
16. `constraints`
17. `negative_prompt`

锁定合同只出现一次；模块用 `preserve` 引用与本改动最相关的部分，不复制整段合同。

## 2. 每个模块的五段式

```json
{
  "goal": "一句话描述可见结果",
  "authorized_area": "可被修改的语义区域或显式遮罩",
  "preserve": ["关键保留项"],
  "change": {
    "subject": "改动对象",
    "anchor": "相对原图可定位的锚点",
    "appearance": "材质、颜色、形态、强度与单一时间相位"
  },
  "integrate": {
    "perspective": "如何服从原透视",
    "occlusion": "前后遮挡",
    "lighting": "受光、发光、接触影或反射",
    "depth_and_grain": "景深、锐度、噪点与颗粒"
  },
  "acceptance": ["可观察的通过条件", "失败时只重试的区域"]
}
```

字段可扩展，但不要删去 `authorized_area/preserve/change/integrate/acceptance`。

## 3. 语义蒙版写法

语义区域必须能由原图定位，优先使用：

- 对象 + 方位：`人物右后方的路人，不含人物发丝边缘`。
- 锚点 + 尺度：`以双脚中点为圆心、约 0.9 个肩宽的地面椭圆区`。
- 边界 + 羽化：`沿原天空—建筑轮廓，发丝边缘保留 2–4px 过渡观感`。
- 曲面：`仅在黑色丝袜现有覆盖区内，沿腿部曲率和原织纹方向`。

不要使用无法落图的“周围一点”“合适位置”“高级区域”。没有图时写“执行时先检测……再建立遮罩”，不编坐标。

## 4. 正向目标与负面约束

先描述期望终态，再补最少的排除项：

- 好：`移除指定路人后，该区域连续呈现原墙面接缝和同深度散景；人物及其发丝轮廓保持原样。`
- 弱：`去路人，不要改人，不要糊，不要假，不要重画。`

`negative_prompt` 只放与本次最相关的 8–20 项，按优先级排列：身份漂移、额外肢体、遮罩泄漏、透视错误、错误遮挡、无接触影、贴纸感、过曝、锐度/颗粒不匹配、乱码文字等。模块内部不重复同一串负面词。

## 5. 复杂度与 pass_plan

`execution_strategy`：

- `single_pass`：总风险分 ≤6、没有互相开放同一锁定维度的冲突模块。
- `ordered_micro_passes`：总风险分 >6，或同时涉及结构修复、多个自发光效果、全局成片、精确文字等。
- `checkpointed_multi_turn`：执行器明确支持连续编辑，且复杂任务需要每轮验收后再继续；每步写检查点、继续条件和失败回滚点。

推荐步骤：

1. `repair_pass`：清理、补洞、伪影、手脚/假发/服装结构。
2. `subject_finish_pass`：修脸、塑形、肤质、妆面、丝袜与服装质感。
3. `blend_addition_pass`：多图溶图、实体增材、角色特征、影子和特效；每个供体独立定位和 warp。
4. `harmonize_lighting_pass`：仅在新增内容光色不一致时协调，再执行虚拟打光；逐灯重建受光和投影。检测到无来源白边/色溢时才插入边缘修复，不删除真实轮廓光或 VFX 辉光。
5. `global_finish_pass`：虚化、空气透视、调色、镜头效果、海报/边框/文字；成像不一致才启用 `capture_match_plan`，交付锐化最后执行。

只列实际需要的步骤。每步写 `input_basis: previous_pass_output`、本步模块、授权区、保持区和验收。某一步失败只重做该步与该区，不重跑所有操作。

暗光救片默认由 `low_light_rescue` 吸收降噪；只有明确超分、普通失焦或运动模糊时再叠加 `enhance_plan`。`hair_fix` 只处理结构，单纯提升假发材质走 `material_texture_enhance_plan`。已有光影重排用 `lighting_reshape`，新增可定位灯源用 `virtual_lighting_plan`，特效自发光只在 effect 的 `vfx_relight_mask` 内传播。

## 6. 参考图职责

有参考图时写 `reference_roles[]`：

```json
{
  "index": 1,
  "role": "identity | costume | prop | color | composition | typography",
  "use": "仅借用什么",
  "do_not_transfer": ["不得搬入的内容"]
}
```

一个参考图可以有多个明确角色，但不要写笼统的“全部参考”。身份参考优先于风格参考；用户原图永远是姿态、坐标和几何基准。

## 7. 精确文字策略

`text_plan` 必须包含：`exact_text/language/case/punctuation/font_genre/hierarchy/alignment/safe_area/render_text/fallback`。

- 用户没有给准确文案时不要自行编角色名或署名。
- `text_rendering=unknown` 或用户要求零错字时，`render_text=false`，只生成留白与排版说明。
- 允许模型渲染时，文案尽量短；验收逐字符比对。错误只重试文字区，不重画人物与背景。

## 8. 验收与重试

`acceptance_tests` 至少覆盖：

- 身份/人数/姿态/坐标是否保持。
- 未授权区域是否出现可见变化；有宿主工具时做差分检查。
- 透视、遮挡、尺度、接触影和光照方向是否合理。
- 新增内容的景深、锐度、噪点、色散和颗粒是否匹配同深度原内容。
- 文案逐字符、手足解剖、服装覆盖等模块专项检查。

`retry_policy`：指出失败项对应的最小遮罩与可修改字段；最多建议 3–5 个候选用于选优，但不要声称多次生成必然解决。
