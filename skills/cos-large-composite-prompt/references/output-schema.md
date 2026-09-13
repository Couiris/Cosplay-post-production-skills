# 两阶段输出格式

两份外层预设均包含 `id/title/content/params/category/subCategory/refImages/_isFactory`。content 是转义后的单行 JSON 字符串。

## 共同内层字段顺序

1. `role_instruction`
2. `mode_and_stage`
3. `character_worldview_card`
4. `geometry_contract`
5. `camera_calibration`
6. `subject_perspective_lock`
7. `subject_scene_scale_contract`
8. `scene_layers`
9. `subject_light_profile`
10. `environment_light_plan`
11. `light_interaction_regions`
12. `light_consistency_validation`
13. `light_match_strength`
14. `integration`
15. `validation`
16. `constraints`

阶段 1 另含 `subject_shadow_composite`、`subject_lock_contract`、`stage1_execution_contract`、`shadow_controls`、`base_frame_manifest` 与 `shadow_lock_package`，负责输出背景板、独立影子层，并由宿主按原始抠图绝对坐标回贴人物。阶段 2 另含 `subject_removed_refined_plate`、`base_frame_lock`、`stage2_execution_contract`、`shadow_removal_contract`、`stage2_asset_expansion`、`background_refinement`、`background_vfx` 与 `deferred_foreground_vfx`，负责输出无人物、无影子的局部补洞和透明叠加层，再由宿主确定性合成。阶段 1 人数等于实际输入；阶段 2 必须为 0。

## 五层参数

每份预设都提供 number 0–100、step 5：

- `ground_richness` / `ground_detail`
- `airborne_richness` / `airborne_detail`
- `foreground_richness` / `foreground_detail`
- `midground_richness` / `midground_detail`
- `background_richness` / `background_detail`

target 精确指向内层实际字段。阶段 1 提供 `contact_shadow/cast_shadow/ambient_occlusion`，默认 60/50/50。阶段 2 提供 `shadow_removal_strength/asset_expansion_intensity/material_refinement/background_vfx_intensity/background_particle_density`，默认 100/65/75/55/50；其中影子移除参数固定为 `min: 100, max: 100, default: 100`。阶段 2 参数不得改变人物移除 mask、场景骨架、主资产、灯位或景深。不得提供 `edge_blend`。

两份预设都提供 `light_match_strength`，number 0–100、step 5、默认 90、target 为同名顶层字段。它只控制环境对人物原光的贴合严格度。

## 光源字段与两阶段复用

- 字段结构、证据等级、13 类光源素材和拒绝规则统一读取 [环境光源反推](lighting-reconstruction.md)。
- 阶段 1 以原始人物作为拍摄角度、承重点和光照参考，先建立 `subject_light_profile`，再确定新场景光源，并在 alpha 外生成与实际光源一致的影子；人物像素由宿主回贴。
- 阶段 2 禁止改变或重新设计光源；`subject_light_profile`、`environment_light_plan` 与 `light_match_strength` 必须与阶段 1 逐字段相同。同时必须从阶段 1 实际输出背景建立 `background_light_evidence`，记录窗、太阳、天空、顶灯、自发光物、反射和已有环境投影的方向、高度、面积、软硬、颜色、强度、衰减与遮挡，并与冻结计划交叉验证。
- `light_interaction_regions` 在阶段 1 包含人物核心锁定、承重点和影子区；阶段 2 将人物 alpha 与阶段 1 影子差分都定义为移除区，用户后期可从独立影子层擦回。
- 阶段 1 的 `shadow_lock_package` 必含画布同尺寸 `locked_shadow_mask`、`shadow_reference_pixels`、三个影子分区、`exclude_subject_pixels: true` 与透明独立影子层。
- 阶段 1 的 `base_frame_manifest` 必含阶段 1 原图引用/哈希、画布尺寸、人物移除遮罩，以及 asset/refinement/vfx 三类绝对坐标授权遮罩。
- 阶段 1 的 `subject_lock_contract` 必含原始透明人物引用、绝对坐标、alpha/bbox/质心/脚点/宽高/旋转和RGBA哈希，并声明 `subject_transform_allowed: false`、`subject_repaint_allowed: false`、`subject_model_output_allowed: false`。
- 阶段 1 的 `stage1_execution_contract` 必须声明 1A 只输出 `background_plate_rgba`、1B 只输出不含人物像素的 `shadow_layer_rgba`、1C 由宿主从背景板复制开始按原始alpha回贴人物再合成影子；模型人物整图输出直接拒绝。
- 阶段 2 的 `shadow_removal_contract` 必含 `shadow_removal_strength: 100`、`source_mask: "locked_shadow_mask from stage1"`、`shadow_removal_mask = locked_shadow_mask`、`no_restore: true` 与无影残留验收；阶段 1 独立影子层只交给用户后期擦回。
- 阶段 2 的 `base_frame_lock` 必含 `immutable_base_image: "stage1_output"`、`global_generative_render: false`、`transform_allowed: false` 与 `mask_coordinates: "canvas_absolute"`。
- 阶段 2 的 `stage2_execution_contract` 必须声明 2A 只输出补洞 patch、2B 只输出透明素材/材质/特效层、2C 由宿主确定性合成；所有补丁/叠加层在授权遮罩外 alpha=0，禁止采用模型全画幅输出。
- `authorized_change_mask = subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask`；其补集 `unchanged_region_mask` 与阶段 1 的 RGBA 差分必须为 0。
- `stage2_asset_expansion` 的新增素材只进入人物 alpha、识别净区和人物/影子移除区之外，并逐件提供世界观、尺度、透视、材质、景深、遮挡和光影。
- `light_consistency_validation` 拒绝灯位漂移、实际背景与冻结计划冲突、反向投影、无来源色温和错误遮挡。阶段 1 另拒绝人物核心像素改变；阶段 2 另拒绝任何可见人物像素和影子残留。

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

外层可解析；content 反转义后可解析；所有 target 存在；布尔/数字/数组类型正确；无注释、尾逗号、占位符和省略号。两阶段 geometry/camera、subject_light_profile、environment_light_plan 与 light_match_strength 逐项相同；阶段 1 `subject_count` 等于输入实际人数并产出完整人物锁合同、manifest 与影子锁包，回贴后人物RGBA与原始抠图零差异；阶段 2 必须为 0、无人物影子，禁止全画幅生成式成片，`shadow_removal_mask` 内无影子残留，未授权区域 RGBA 差分为零；新增素材、材质和特效均不得触碰授权遮罩外底图。
