# 输出格式与摄影匹配

每次输出前读取。最终两份预设必须分别是合法 JSON；外层 content 是内层指令对象的单行转义 JSON 字符串。照片保真、清场和扩图字段读取 [照片保真、清场与可选扩图合同](photo-fidelity-cleanup.md)。

## 两阶段外层信封

字段必须包含：

- 阶段 1 id：`f_scene_<slug>-step1-subject-shadow-composite`
- 阶段 2 id：`f_scene_<slug>-step2-subject-removed-refined-plate`
- title：分别标明“阶段1：人物影子合成”和“阶段2：无人无影精修底板”
- content：下述内层对象的转义字符串
- params：人工控制项
- category：scene
- subCategory：场景中文名
- refImages：空数组
- _isFactory：true

两份 params 都提供下列真实 target；阶段 2 的五层参数读取并锁定阶段 1 的几何，只控制授权遮罩内的新增与细化：

- ground_scope -> scene_layers.ground.scope，枚举 local_around_subject / full_venue
- ground_richness -> scene_layers.ground.richness
- foreground_richness -> scene_layers.foreground.richness
- midground_richness -> scene_layers.midground.richness
- background_richness -> scene_layers.background.richness
- airborne_richness -> scene_layers.airborne.richness
- ground_detail、foreground_detail、midground_detail、background_detail、airborne_detail -> 对应层 detail_precision
- depth_strength -> camera_match.depth_strength
- blend_strength -> integration.blend_strength
- light_match_strength -> light_match_strength，number 0–100，step 5，默认 90
- canvas_mode -> canvas_expansion_contract.mode，枚举 original_canvas / expand_if_needed，默认 original_canvas
- expansion_margin_percent -> canvas_expansion_contract.max_margin_percent，number 0–30，step 5，默认 15；仅 canvas_mode=expand_if_needed 时生效
- 阶段 1：contact_shadow、cast_shadow、ambient_occlusion -> `shadow_controls` 对应真实字段
- 阶段 2：shadow_removal_strength -> `shadow_removal_contract.shadow_removal_strength`，固定 100
- 阶段 2：material_refinement、background_vfx_intensity、background_particle_density -> 对应真实字段

丰富度与精细度使用 number 0–100，step 5。richness 映射 0/25/50/75/90/100，detail_precision 映射 0/25/50/75/90/100。房间类 background_richness 默认 0。

## 共享内层对象顺序

1. role_instruction：必须是内层第一个键，值以“现在你是一个资深 COS 后期合成师，你需要去做一次 COS 后期合成，生成一个场景，并让人物主体自然融入生成的场景。”开头。
2. priority_order：photographic_fidelity_contract、geometry_contract、canvas_expansion_contract、subject_perspective_lock、original_scene_geometry_lock、camera_calibration、ground_plane_registration、subject_scene_scale_contract、subject_light_profile、environment_light_plan、cleanup_contract、scene_layers、vfx。
3. character_context：source_and_character、verified_background、personality、scene_rationale、confidence。
4. photographic_fidelity_contract：原照片基础、原材质、原构图、原光影、明度、色相、饱和度、伽马、对比度、色调曲线和成像锁定。
5. cleanup_contract：阶段 1 清除非主角人物、全部临时摄影器材与主角背后杂物；阶段 2 清除主角及影子/倒影/残留，并规定原材质补洞。
6. canvas_expansion_contract：默认 original_canvas；需要扩图时记录原画框、最终画布、四边扩展量、outpaint_mask 与 1:1 嵌入规则。
7. geometry_contract：输入宽高、比例、方向与画布禁改项；启用扩图时只允许原画框之外增加像素。
8. subject_perspective_lock：人物 alpha 边界框、中心、头顶、脚点/承托点、武器端点、宽高占比、旋转和零容差。
9. original_scene_geometry_lock：保留墙、地面、栏杆、门框、立柱、钢架等线段与遮挡关系。
10. ground_plane_registration：至少四条地面证据、平面单应性、承重点和尺度参照。
11. subject_scene_scale_contract：人物身高=1.0，头宽/肩宽/手掌/脚长，地面纹理和至少两个同深度参照物。
12. hard_locks：
   - subject：人物身份、脸、五官、表情、妆面、肤色、发型发色、发丝、服装、配饰、武器不变。
   - pose：人数、动作、姿态、肢体角度、视线、手势不变。
   - transform：原 X/Y、中心点、脚点、宽高、旋转角、大小、占比不变。
   - canvas：默认分辨率和宽高比不变；可选扩图只新增外部像素，原画框 1:1 锁定，禁止裁切、缩放、旋转、移动或重采样。
   - venue：背景墙、天花板、顶灯、钢架/桁架不替换、不重绘、不覆盖。
   - original_color：人物与原景保留区色相、饱和度、亮度、白平衡、黑白位、伽马、对比度、色调曲线和高光不变，禁止全局调色。
13. retained_original_scene：分别列 wall、ceiling、roof_truss、lights、other_regions，preservation_precision 固定 high，color_lock true。
14. scene_layers：ground、foreground、midground、background、airborne 分开，每层包含 enabled、richness、detail_precision、elements、placement、occlusion、perspective_contract、scale_contract、focus_blur_contract、lighting_and_shadow；ground 另含 scope、contact_and_transition。
15. camera_match：focal_length、aperture_dof、viewpoint、horizon_and_vanishing_points、lens_rendering、depth_strength、evidence、confidence。用户未给拍摄参数时必须视觉估计；单张图不能唯一反推真实 EXIF，因此给范围并标“以原片为准”。
16. subject_light_profile：按 [环境光源反推](lighting-reconstruction.md) 的统一结构，分别记录主光、辅光、轮廓光、环境光与可能自发光；每个光源包含方向、高度、软硬、相对面积、色温/色偏、强度比、证据和置信度。优先引用保留区的可见顶灯、舞台灯、窗和灯架；证据不足时用范围与低置信度。
17. environment_light_plan：把人物原光映射到画内/画外的太阳、窗、棚灯、路灯、霓虹、火焰或法阵；含 visible_fixture_consistency、distance_falloff、occlusion、lit/unlit surfaces、shadows、reflections、volumetrics。新增灯只补充或解释原光，不能与保留灯具冲突。
18. light_interaction_regions：subject_core 锁定；edge_band 与可达表面仅在光路、距离和遮挡允许时接受克制溢色；遮挡面禁止受光。
19. light_consistency_validation：逐项核验鼻影/原投影方向、色温来源、阴影软硬、可见灯具、距离衰减、遮挡和全身染色；任何矛盾写 reject。
20. light_match_strength：整数 0–100，默认 90，只控制环境向人物原光贴合的严格程度，不修改人物核心像素。
21. integration：blend_strength、edge_band、texture_match、depth_order。
22. perspective_validation：画布、人物变换、原景线、地平线、灭点、脚点、遮挡和尺度的拒绝条件。
23. 阶段执行对象：阶段 1 使用 `subject_lock_contract/stage1_execution_contract/shadow_lock_package/base_frame_manifest/asset_geometry_lock`；阶段 2 使用 `subject_count/base_frame_lock/stage2_execution_contract/shadow_removal_contract/background_only_contract/stage2_asset_refinement_manifest/stage2_asset_expansion`。
24. constraints.must_not：动态严禁项数组。

两阶段都必须把上述共享字段完整写入各自 `content`，禁止使用“同阶段1”或引用代替。详细遮罩、透明层和宿主合成规则读取 [半合成两阶段流程](two-stage-workflow.md)。

每个 elements 条目都包含：

- element：物体名称。
- worldbuilding_basis：与角色时代、地域、组织、职业、能力体系或剧情时刻的关系及证据置信度。
- geometry_and_scale：实际尺度、朝向、厚度、与人物比例。
- material_surface：材质、纹理方向、接缝、边缘、磨损/洁净、粗糙度、反射或半透明。
- placement：画面区域、前后关系、是否落地。
- camera_rendering：同深度清晰度、景深、运动模糊和畸变匹配。
- light_and_shadow：受光方向、接触影、投射影、环境遮蔽、反射。
- preserve_and_avoid：不可遮挡或修改的主体与原景。

高 detail_precision 时展开全部字段；中等可合并表达；低精度至少保留 element、placement、scale、material 和 light_and_shadow。

## 焦段、光圈与景深

- 有可靠 EXIF 写精确值；无 EXIF 使用“视觉估计，以原片为准”。
- 广角全身示例：视觉估计约 24–35mm 等效；保持边缘轻微拉伸与地面纵深。视觉近似 f/4–5.6，人物全身和脚点清楚，中景略软，远墙柔化但钢架线条可辨。
- 标准视角示例：视觉估计约 40–60mm 等效；视觉近似 f/2.8–4，人物面部与同平面中景清楚，前景轻虚、远景中度虚化。
- 中长焦半身示例：视觉估计约 85–135mm 等效；视觉近似 f/1.8–2.8，眼睛/面部在焦平面，前景和远墙渐进虚化，散景大小匹配原片。
- 画面证据优先。新增物锐度不得高于同一深度的原内容。

## 光源和阴影匹配

完整字段、光型素材库与拒绝规则见 [环境光源反推](lighting-reconstruction.md)。

- 方向：用人物鼻影、下颌影、服装褶皱高光、武器反光和已有落地影交叉判断，避免只凭最亮区域猜测。
- 色温：分别记录主光和环境填充的冷暖关系。新增素材允许承接相同冷暖，不得改变人物肤色、服装和原景颜色。
- 亮度：以人物面部中间调和白色服装高光作为相对基准，限制新增物不抢主体、不无故过曝或死黑。
- 软硬：人物阴影边缘柔和时，新影保持大光源的软边；人物影边锐利时，新影才使用硬边。
- 投影：落地物必须有接触影；悬浮物只在物理合理且原光支持时投影。影子沿原主光反方向延伸，并匹配距离造成的软化。
- 反射：湿地、金属、玻璃、水面只反射实际可见光源与邻近颜色；不得生成不存在的霓虹或窗口倒影。
- 可见灯具：保留场馆灯具是最高优先级证据；清理灯架或灯体时也必须保留它对人物原光的等效画外光源解释。

## 室内强制项

房间类 scene_layers.background.enabled 固定 false，除非用户只要求不接触墙面的低矮落地物；即使开启也不得把墙/顶替换为壁炉、护墙板、窗户或建筑。所谓壁炉、书架、屏风、窗景等只能作为独立可移动景片或摆件置于墙前，并保留可见边界与真实落地阴影。

## 动态严禁项

至少包含：阶段 1 改变人物或其动作/位置/大小/占比；缩放、旋转、重采样或重构原画框；替换或重绘墙与顶；改变保留区原材质、明度、色相、饱和度、伽马、对比度、色调曲线、焦段观感、焦平面、景深、透视或机位；残留路人、摄影器材、主角、人物影子、倒影、残影；白边、悬浮、穿模、错误接触影、重复肢体、乱码、文字或水印。再根据所选元素追加 2–5 条具体风险。

## 合法性检查

两份外层都能解析；content 反转义后也能解析；params target 对应真实字段；数组、布尔和数值类型正确；没有注释、尾逗号、占位符或省略号。`cleanup_contract` 默认包含非主角人物、临时摄影器材和主角背后杂物；用户明确保留的对象进入 `cleanup_keep_whitelist`。阶段 1 人物来自宿主原始 RGBA 回贴；阶段 2 `subject_count` 固定为 0、`shadow_removal_strength` 固定为 100，且不存在模型全画幅输出路径。
