# 输出格式与合法性

最终交付一个合法 JSON 对象。`content` 是内层指令对象经 `JSON.stringify` 得到的单行字符串；不是嵌套对象、Markdown 或伪代码。

## 1. 外层信封

八个键全部必需：

```json
{
  "id": "f_vfx_gold-magic-circle",
  "title": "脚下金色法阵",
  "content": "{\"role_instruction\":\"...\"}",
  "params": [],
  "category": "vfx",
  "subCategory": "法阵",
  "refImages": [],
  "_isFactory": true
}
```

- `id`：`f_<category>_<kebab-slug>`，只用小写英数与连字符。
- `title`：简短中文，说明主要结果。
- `params`：只列启用模块所需的滑块。
- `category`：`vfx/cleanup/enhance/retouch/hair/grading/blur/prop/outfit/sky/outpaint/poster/frame/stylize/combo`。
- `refImages`：没有参考图时 `[]`；有参考图时保留插件需要的引用值，并在内层 `reference_roles` 分配职责。

## 2. 内层必需键

建议按下列顺序，便于模型先看到任务和锁定，再看到修改：

1. `role_instruction`
2. `task_summary`
3. `photo_readout`
4. `executor_profile`
5. `execution_strategy`：`single_pass` 或 `ordered_micro_passes`
6. `priority_order`
7. `subject_lock_contract`
8. `geometry_camera_lock_contract`
9. `background_lock_contract`
10. `subject_light_profile`
11. `reference_roles`（仅有参考图时）
12. `pass_plan`（仅 ordered_micro_passes 时）
13. 启用模块，按修复→主体精修→增材/VFX→全局成片排序
14. `authorization_contract`
15. `integration`
16. `acceptance_tests`
17. `retry_policy`
18. `constraints`
19. `negative_prompt`

锁定合同必须声明“目标”与“能力条件”：有显式蒙版/回贴时可要求遮罩外差分为零；只有自然语言整图编辑时写 `best_effort`，不得冒充物理保证。

## 3. 模块字段

全部模块必须含：

```json
{
  "goal": "可见结果",
  "authorized_area": "语义区域或显式遮罩",
  "preserve": ["关键保留项"],
  "change": {},
  "integrate": {},
  "acceptance": ["通过条件", "局部重试范围"]
}
```

`vfx_plan` 另外含 `render_style/particle_density/effects[]`。每个 effect 必含：

`effect_id/type/variant/source_and_cause/vfx_zone/authorized_area/anchor/depth_order/visual_description/material_emission/dynamics/environment_interaction/camera_response/intensity/relight_and_blend/anti_sticker/acceptance`

其中 `depth_order` 只能是 `behind_subject/around_subject/in_front_of_subject`。自发光效果还必须有 `vfx_relight_mask`，写可达面、染色色、亮度上限、距离衰减和遮挡终止。

`virtual_lighting_plan.change.lights[]` 每盏灯必含 `light_id/role/motivation/source_position/direction_and_elevation/color/hardness/spread/intensity/distance_falloff/affected_surfaces/shadow_behavior/exclude`。

`image_blend_plan.change` 必含 `base_image/donor_images/alignment/blend_method/opacity_or_strength/transition_zone/color_harmonization/depth_and_occlusion/seam_healing`；每个供体图必含 `ref/transfer_only/do_not_transfer`，并在外层 `refImages` 与内层 `reference_roles` 中可追溯。

## 4. params

每项含 `key/label/type/min/max/default/step/target`，`type` 为 `number`。target 必须真实存在；`[]` 表示数组中每项。

| key | 默认 | target |
|---|---:|---|
| `vfx_intensity` | 60 | `vfx_plan.effects[].intensity` |
| `emission_strength` | 55 | `vfx_plan.effects[].material_emission.strength` |
| `particle_density` | 45 | `vfx_plan.particle_density` |
| `blend_strength` | 60 | `integration.blend_strength` |
| `light_match_strength` | 90 | `subject_light_profile.light_match_strength` |
| `depth_strength` | 60 | `integration.depth_match.strength` |
| `texture_strength` | 55 | `material_texture_enhance_plan.change.strength` |
| `enhance_strength` | 55 | `enhance_plan.change.strength` |
| `retouch_strength` | 45 | `face_retouch.change.strength` |
| `sculpt_strength` | 50 | `body_sculpt.change.strength` |
| `sheen_strength` | 55 | `body_finish.change.sheen_strength` |
| `hosiery_sheen` | 50 | `hosiery_fix.change.sheen` |
| `wind_degree` | 45 | `hair_flow_plan.change.degree` |
| `grading_strength` | 50 | `grading_plan.change.strength` |
| `blur_strength` | 35 | `blur_plan.change.strength` |
| `lens_fx_strength` | 35 | `lens_fx_plan.change.strength` |
| `virtual_light_intensity` | 50 | `virtual_lighting_plan.change.lights[].intensity` |
| `blend_opacity` | 55 | `image_blend_plan.change.opacity_or_strength` |
| `harmonize_strength` | 60 | `subject_harmonize_plan.change.strength` |
| `low_light_strength` | 50 | `low_light_rescue.change.strength` |
| `atmosphere_strength` | 35 | `depth_atmosphere_plan.change.strength` |
| `poster_grade` | 60 | `poster_plan.change.strength` |
| `stylize_strength` | 60 | `stylize_plan.change.strength` |

默认值必须与内层数值相同。0–33 表示轻，34–66 表示中，67–100 表示强；不是所有模块都需要滑块。

## 5. execution_strategy

`single_pass`：直接执行模块顺序。

`ordered_micro_passes`：`pass_plan[]` 每项含：

```json
{
  "pass_id": "repair_pass",
  "input_basis": "original_input 或 previous_pass_output",
  "modules": ["cleanup_plan"],
  "authorized_area": "本步授权并集",
  "preserve": ["本步只读内容"],
  "acceptance": ["本步通过条件"]
}
```

外层仍是一份预设；`pass_plan` 是执行建议。若插件只能单次运行，按数组顺序在同一次推理中处理，但优先保护高优先级锁定。

## 6. authorization_contract

至少包含：

- `per_module`：每模块的授权区、深度与边缘策略。
- `authorized_change_mask`：授权区并集的文字定义。
- `unchanged_region_mask`：并集之外的只读目标。
- `mask_enforcement`：`explicit_mask | semantic_mask | host_composite`。
- `lock_reliability`：`strong | best_effort`。
- `face_clean_zone`：除面部专项模块外保持干净。

## 7. 验证清单

1. 外层可解析，`content` 反序列化后仍是对象。
2. 八个外层键、内层必需键齐全；没有注释、尾逗号、省略号或占位符。
3. 启用模块都在 [模块注册表](module-registry.md)，每项含五段式字段。
4. `params.target` 能解析到真实数值；默认值与内层一致。
5. `ordered_micro_passes` 必须有非空 `pass_plan`；`single_pass` 不需要空的 `pass_plan`。
6. 特效字段、深度枚举和自发光 relight 信息齐全。
7. 授权区覆盖所有模块；锁定可靠性与执行器能力一致。
8. 身份、手足、文字、服装覆盖、透视、遮挡、光影、景深、噪点分别有验收项。

保存文件后运行 `python scripts/validate_preset.py <preset.json>`。
