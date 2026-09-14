# 两阶段输出格式

两份外层预设均包含 `id/title/content/params/category/subCategory/refImages/_isFactory`。content 是转义后的单行 JSON 字符串。

## 共同内层字段顺序

1. `role_instruction`
2. `intent_card`
3. `executor_profile` 与 `execution_status`
4. `pair_id`、`pair_manifest` 与 `runtime_bindings`
5. `reference_roles`（有参考图时）
6. `mode_and_stage`
7. `character_worldview_card`
8. `geometry_contract`
9. `camera_calibration`
10. `subject_perspective_lock`
11. `subject_scene_scale_contract`
12. `scene_layers`
13. `subject_light_profile`
14. `environment_light_plan`
15. `light_interaction_regions`
16. `light_consistency_validation`
17. `light_match_strength`
18. `integration`
19. `validation`
20. `constraints`

阶段 1 另含 `subject_shadow_composite`、`subject_lock_contract`、`stage1_execution_contract`、`shadow_controls`、`base_frame_manifest` 与 `shadow_lock_package`，负责输出背景板、独立影子层，并由宿主按“背景→影子→原人物”回贴。阶段 2 另含 `subject_removed_refined_plate`、`base_frame_lock`、`stage2_execution_contract`、`shadow_removal_contract`、`stage2_overlay_layers`、`stage2_asset_expansion`、`background_refinement`、`background_vfx` 与 `final_assembly_manifest`，负责输出无人物、无影子底板及透明叠加层。阶段 1 人数等于实际输入；阶段 2 必须为 0。

`execution_status=executable` 要求 `executor_profile.subject_cutout_available/mask_support=explicit/rgba_patch_output/absolute_coordinate_composite/pixel_diff_validation` 全部满足；参考图非空时另要求多参考能力已确认。能力不足只输出 `blocked_by_capability` 诊断。无法在生成时填入的真实坐标与 hash 使用类型化 `runtime_bindings[]`，每项含 `binding/type/resolver/required_before_stage`，执行前必须解析完成。

## 五层参数

阶段 1 提供 number 0–100、step 5 的主场景参数：

- `ground_richness` / `ground_detail`
- `airborne_richness` / `airborne_detail`
- `foreground_richness` / `foreground_detail`
- `midground_richness` / `midground_detail`
- `background_richness` / `background_detail`

target 精确指向内层实际字段。阶段 1 另提供 `contact_shadow/cast_shadow/ambient_occlusion`，默认 60/50/50。阶段 2 的 `scene_layers` 是只读快照，新增层使用 `overlay_<layer>_richness/overlay_<layer>_detail -> stage2_overlay_layers.<layer>.richness/detail_precision`；另提供 `shadow_removal_strength -> shadow_removal_contract.shadow_removal_strength`、`asset_expansion_intensity -> stage2_asset_expansion.asset_expansion_intensity`、`material_refinement -> background_refinement.material_refinement`、`background_vfx_intensity -> background_vfx.background_vfx_intensity`、`background_particle_density -> background_vfx.background_particle_density`，默认 100/65/75/55/50，其中影子移除固定为 `min=max=default=100`。阶段 2 参数不得改变人物移除 mask、场景骨架、主资产、灯位或景深。不得提供 `edge_blend`。

两份预设都提供 `light_match_strength`，number 0–100、step 5、默认 90、target 为同名顶层字段。它只控制环境对人物原光的贴合严格度。

## 光源字段与两阶段复用

- 字段结构、证据等级、13 类光源素材和拒绝规则统一读取 [环境光源反推](lighting-reconstruction.md)。
- 阶段 1 以原始人物作为拍摄角度、承重点和光照参考，先建立 `subject_light_profile`，再确定新场景光源，并在 alpha 外生成与实际光源一致的影子；人物像素由宿主回贴。
- 阶段 2 禁止改变或重新设计光源；`subject_light_profile`、`environment_light_plan` 与 `light_match_strength` 必须与阶段 1 逐字段相同。同时必须从阶段 1 实际输出背景建立 `background_light_evidence`，记录窗、太阳、天空、顶灯、自发光物、反射和已有环境投影的方向、高度、面积、软硬、颜色、强度、衰减与遮挡，并与冻结计划交叉验证。
- `light_interaction_regions` 在阶段 1 包含人物核心锁定、承重点和影子区；阶段 2 将人物 alpha 与阶段 1 影子差分都定义为移除区，用户后期可从独立影子层擦回。
- 阶段 1 的 `shadow_lock_package` 必含画布同尺寸 `locked_shadow_mask`、`shadow_reference_pixels`、影子分区、`exclude_subject_pixels: true` 与透明独立影子层。无可见承载面或人物悬空时 `shadow_mode: none` 并提供 `no_shadow_reason`，不得伪造脚底黑影；多人共享影子时记录 `caster_ids`。
- 阶段 1 的 `base_frame_manifest` 必含阶段 1 原图引用/哈希、画布尺寸、人物移除遮罩，以及 asset/refinement/vfx 三类绝对坐标授权遮罩。
- 阶段 1 的 `subject_lock_contract.subjects[]` 必须逐人记录 `subject_id/source/alpha/bbox/centroid/crown/contact_points/width_height/rotation/pixel_hash/occlusion_order`，并声明 `subject_transform_allowed: false`、`subject_repaint_allowed: false`、`subject_model_output_allowed: false`；`union_subject_alpha` 是阶段 2 人物移除基准。
- 阶段 1 的 `stage1_execution_contract` 必须声明 1A 只输出 `background_plate_rgba`、1B 只输出不含人物像素的 `shadow_layer_rgba`、1C 由宿主从背景板复制开始先合成影子再按原始 alpha 回贴人物；模型人物整图输出直接拒绝。
- 阶段 2 的 `shadow_removal_contract` 必含 `shadow_removal_strength: 100`、`source_mask: "locked_shadow_mask from stage1"`、`shadow_removal_mask = locked_shadow_mask`、`no_restore: true` 与无影残留验收；阶段 1 独立影子层只交给用户后期擦回。
- 阶段 2 的 `base_frame_lock` 必含 `immutable_base_image: "stage1_output"`、`global_generative_render: false`、`transform_allowed: false` 与 `mask_coordinates: "canvas_absolute"`。
- 阶段 2 的 `stage2_execution_contract` 必须声明 2A 只输出补洞 patch、2B 只输出透明素材/材质/特效层、2C 由宿主确定性合成；所有补丁/叠加层在授权遮罩外 alpha=0，禁止采用模型全画幅输出。
- `authorized_change_mask = subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask`；其补集 `unchanged_region_mask` 与阶段 1 的 RGBA 差分必须为 0。
- `stage2_asset_expansion` 的新增素材只进入人物 alpha、识别净区和人物/影子移除区之外，并逐件提供世界观、尺度、透视、材质、景深、遮挡和光影。
- `light_consistency_validation` 拒绝灯位漂移、实际背景与冻结计划冲突、反向投影、无来源色温和错误遮挡。阶段 1 另拒绝人物核心像素改变；阶段 2 另拒绝任何可见人物像素和影子残留。
- `vfx_stage_assignment`：改变天空/主结构/主光源的结构性 VFX 放阶段 1；背景侧透明后效放阶段 2；人物局部染光与压人物前的内容分别输出 `subject_relight_overlay_rgba` 和 `foreground_occluder_rgba`，进入 `final_assembly_manifest`，不修改人物源层。

## 相机与尺度字段

`camera_calibration` 必含 focal_length_estimate、aperture_dof_estimate、camera_height、pitch、roll、yaw、horizon、vanishing_points、lens_behavior、focus_plane、evidence、confidence，以及 `angle_lock`、`angle_validation`。阶段 1 先锁定原片拍摄角度，再生成背景；用户未给值时使用视觉范围和“以原片为准”。人物脚点、视线高度、地平线、两组环境直线和身体透视缩短是优先证据。

`subject_scene_scale_contract` 必含人物身高=1.0、头宽/肩宽/手掌/脚长参照、地面纹理尺度、至少两个同深度场景参照物和 `scale_validation`。

## 每层字段

`enabled/depth_zone/richness/detail_precision/elements/perspective_contract/scale_contract/focus_blur_contract/lighting_and_shadow/occlusion`。

每个元素包含 `element/worldbuilding_basis/depth_and_placement/geometry_and_scale/material_surface/perspective/focus_and_blur/light_and_shadow/preserve_and_avoid`。

两阶段均必须包含 `material_richness_contract`：

- `definition`：独立素材族、实例密度、深度覆盖、材质/形态变化四项综合，不等于全屏堆满。
- `scale`：0–20 必要主资产；21–40 主资产+1辅助族；41–60 2–3辅助族并覆盖三层；61–80 4–6辅助族并覆盖五层；81–100 英雄级多族多实例，超过90逐项列出且保留负空间。
- `stage1_scope`：优先稳定主结构、承托、透视、光影和第一批基础素材。
- `stage2_scope`：只在授权空区增加第二批局部素材、材质变化和透明特效；不得改变天空、建筑、道路或主轮廓。

## 合法性

外层可解析；content 反转义后可解析；pair_id、执行器档案、共享合同与参考图引用一致；所有 target 存在；布尔/数字/数组类型正确；无注释、尾逗号、自然语言占位符和省略号。必须解析 `runtime_bindings` 后才能执行。阶段 1 `subject_count` 等于 `subjects[]` 长度，人物**源层** RGBA 与原抠图零差异；视觉染光只存在于独立 relight 层。阶段 2 必须为 0、无人物影子，禁止全画幅生成式成片，`shadow_removal_mask` 内无影子残留，未授权区域 RGBA 差分为零。
