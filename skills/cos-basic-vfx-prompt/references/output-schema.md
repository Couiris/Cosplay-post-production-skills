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

## 2. 内层键序

建议按下列顺序，便于模型先看到任务和锁定，再看到修改：

1. `role_instruction`
2. `task_summary`
3. `intent_card`（可选输出，但组装前必须内部生成）
4. `photo_readout`
5. `executor_profile`
6. `execution_strategy`：`single_pass`、`ordered_micro_passes` 或 `checkpointed_multi_turn`
7. `priority_order`
8. `subject_lock_contract`
9. `geometry_camera_lock_contract`
10. `background_lock_contract`
11. `subject_light_profile`
12. `reference_roles`（仅有参考图时）
13. `pass_plan`（仅多阶段策略时）
14. 启用模块，按修复→主体精修→增材/VFX→全局成片排序
15. `authorization_contract`
16. `integration`
17. `acceptance_tests`
18. `retry_policy`
19. `constraints`
20. `negative_prompt`

锁定合同必须声明“目标”与“能力条件”：有显式蒙版/回贴时可要求遮罩外差分为零；只有自然语言整图编辑时写 `best_effort`，不得冒充物理保证。

`executor_profile` 必含 `target_family/mask_support/multi_reference_support/text_rendering/output_size/lock_reliability`，可加 `multi_turn_support/layer_or_patch_output`。启用 `image_blend_plan` 前必须确认 `multi_reference_support=supported`；能力为 `unknown/unsupported` 时改为宿主分层合成或在确认能力后再生成可执行预设。

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

`effect_id/type/variant/composition_role/source_and_cause/vfx_zone/authorized_area/anchor/depth_order/silhouette_clearance/density_budget/visual_description/material_emission/dynamics/environment_interaction/camera_response/intensity/relight_and_blend/anti_sticker/acceptance`

其中 `depth_order` 只能是 `behind_subject/around_subject/in_front_of_subject`。自发光效果还必须有 `vfx_relight_mask`，写可达面、染色色、亮度上限、距离衰减和遮挡终止。

`density_budget` 含 `coverage_percent/focal_exclusion/distribution`。多效果时每个 effect 另写 `hierarchy_weight`，顶层写 `global_moment/palette_relationship/shared_environment_response`；默认一个主效果，用户明确双主叙事时允许两个 `primary`，同时写 `co_dominant_reason`。

`virtual_lighting_plan.change.lights[]` 每盏灯必含 `light_id/role/motivation/source_position/direction_and_elevation/color/hardness/spread/intensity/distance_falloff/affected_surfaces/shadow_behavior/exclude`。

`image_blend_plan.change` 必含 `base_image/donor_images/alignment/blend_method/opacity_or_strength/transition_zone/color_harmonization/depth_and_occlusion/seam_healing`；每个供体图必含 `ref/transfer_only/do_not_transfer`，并在外层 `refImages` 与内层 `reference_roles` 中可追溯。两个或以上供体还要逐供体写 `source_region/target_region/anchor_map/transform_or_warp/method/strength/transition_zone/depth_and_occlusion/contact_and_shadow`。

`material_texture_enhance_plan.change.materials[]` 每种材质必含 `material_type/zone/source_evidence/source_confidence/micro_texture/roughness/highlight_shape/color_depth/detail_scale/strength/do_not_invent`；没有输入证据的纹理不生成。`low_light_rescue.change.recoverability` 必须为 `reliable/limited/none`，后两者不得虚构暗部细节。两模块同时启用时必须分阶段。

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
| `texture_strength` | 55 | `material_texture_enhance_plan.change.materials[].strength` |
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
| `edge_cleanup_strength` | 50 | `edge_halo_spill_fix.change.strength` |
| `capture_match_strength` | 50 | `capture_match_plan.change.strength` |
| `output_sharpen_strength` | 30 | `output_finish_plan.change.output_sharpening.strength` |

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

`checkpointed_multi_turn`：仅在 `executor_profile.multi_turn_support=true` 时使用。除上述字段外，每个 pass 还必须含：

```json
{
  "checkpoint_required": true,
  "continue_only_if": ["本轮通过条件"],
  "rollback_to": "previous_accepted_output"
}
```

首步 `input_basis=original_input`，后续步为 `previous_pass_output`；全部启用模块必须且只能在一个 pass 中出现。

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
5. 多阶段策略必须有非空 `pass_plan`，顺序、输入来源和模块覆盖正确；`single_pass` 不需要空的 `pass_plan`。
6. 特效的构图职责、轮廓留空、密度、深度和自发光 relight 信息齐全；多效果的层级与共同叙事可验证。
7. 授权区覆盖所有模块；锁定可靠性与执行器能力一致；供体引用均能追溯到 `refImages`。
8. 滑块键不重复，范围、步长和 target 数值合法。
9. 身份、手足、文字、服装覆盖、透视、遮挡、光影、景深、噪点分别有验收项。

保存文件后运行 `python scripts/validate_preset.py <preset.json>`；修改验证器后再运行 `python scripts/test_validator.py`。
