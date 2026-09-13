# 半合成两阶段流程

半合成与大合成共享“背景板、独立影子、局部补丁、透明叠加层、宿主确定性合成”的执行结构，但永久锁定用户点名的原景；未点名时默认锁定场馆远墙、天花板、顶灯、钢梁/桁架、主要立柱、原画框和机位。两阶段同时服从 [照片保真、清场与可选扩图合同](photo-fidelity-cleanup.md)。

## 阶段 1：基础布景板、独立影子层与原人物回贴

阶段 1 固定拆为：

1. `1A_background_plate`：先在 `cleanup_removal_mask AND NOT subject_alpha` 内移除全部非主角人物、摄影师、临时摄影灯架/器材、线缆、箱包和主角背后杂物，只用相邻原场馆材质输出 `cleanup_fill_patch_rgba`；通过清场验收后，再在 `editable_scene_mask AND NOT subject_alpha` 内生成五层基础素材。保留区逐像素不变；人物区输出透明或由宿主遮挡。
2. `1B_shadow_layer`：以原人物、承重点、地面和冻结光源为参考，只输出画布同尺寸透明 `shadow_layer_rgba`。它包含人物接触影、环境遮蔽和投射影，但人物像素 alpha=0。
3. `1C_host_composite`：宿主执行 `output = copy(background_plate_rgba)`，按原始人物 alpha 的绝对坐标逐像素回贴人物，再按影子绝对坐标合成独立影子层。模型不得生成、重绘、移动、缩放或自动对齐人物。

阶段 1 必填：

- `subject_lock_contract`：原始透明人物引用、alpha/bbox、质心、头顶、脚点/承重点、武器端点、宽高、旋转、像素哈希；`subject_transform_allowed: false`、`subject_repaint_allowed: false`、`subject_model_output_allowed: false`。
- `stage1_execution_contract`：1A/1B/1C 的输入、输出、绝对坐标、遮罩公式、宿主合成顺序和失败策略。
- `shadow_lock_package`：`locked_shadow_mask = contact_shadow_mask OR ambient_occlusion_mask OR cast_shadow_mask`；保存 `shadow_reference_pixels`、RGBA、透明度、混合模式和逐像素验收，供用户后期手动擦回。
- `base_frame_manifest`：画布、阶段 1 输出引用/哈希、`cleanup_removal_mask`、`subject_removal_mask`、`locked_shadow_mask`、`asset_addition_mask`、`material_refinement_mask`、`background_vfx_mask`、`outpaint_mask`、原景永久锁 mask 和每个 `asset_id` 的几何锁。
- `photographic_fidelity_contract`、`cleanup_contract` 与 `canvas_expansion_contract`：逐字段记录原材质、原构图、光影、明度、色相、饱和度、伽马、对比度、色调曲线、成像特征、清场对象和可选扩图边界。
- `asset_geometry_lock`：记录每个阶段 1 素材的边界、落点、尺度、朝向、部件拓扑、遮挡和所属深度。阶段 2 只能细化，不能重设计。

阶段 1 验收先于丰富度：回贴后人物 RGBA、alpha bbox、质心、面积、脚点、姿态和武器端点与原始抠图逐通道一致；所有非主角人物和临时摄影器材已经清除；补洞保持原场馆材质；保留场馆区域与输入逐像素一致；影子方向、软硬、颜色、长度和承重点与冻结光源一致。失败只重做对应清理 patch、1A 或 1B，不让模型修人物或保留区。

## 阶段 2：无人无影补洞、透明增材与精修

阶段 2 以阶段 1 输出为不可变底图，禁止模型全画幅生成。固定拆为：

1. `2A_subject_shadow_fill`：只生成画布同尺寸或带绝对坐标的 `subject_fill_patch_rgba`；仅 `subject_removal_mask OR shadow_removal_mask` 内 alpha 可非零。移除主角及与其相连的道具、发丝、配饰、接触影、投射影、环境遮蔽、倒影、反射、残影和人形负空间，补出连续的原场馆材质、地面、景片和空气。输出 `subject_count: 0`，不得保留任何人物或人物影子。
2. `2B_overlay_generation`：分别输出 `asset_overlay_rgba`、`refinement_overlay_rgba`、`vfx_overlay_rgba`。每层只能写入阶段 1 manifest 提供的显式 mask，遮罩外 alpha=0；新增素材不得进入人物/影子补洞区，材质精修不得改变已锁定几何。
3. `2C_host_composite`：宿主执行 `output = copy(stage1_output)`；在人物/影子移除 mask 内覆写 2A 补丁，再按绝对坐标 alpha 合成 2B 各层。禁止任何缩放、旋转、平移、自动对齐、全局调色或模型整图回写；阶段 1 影子不回写。

阶段 2 必填：

- `base_frame_lock`：`immutable_base_image: stage1_output`、`global_generative_render: false`、`transform_allowed: false`、`mask_coordinates: canvas_absolute`，并复用阶段 1 输出哈希与原景永久锁 mask。
- `stage2_execution_contract`：2A/2B/2C、每类 RGBA 输出、宿主合成公式与遮罩外 alpha=0。
- `shadow_removal_contract`：`shadow_removal_mask` 直接读取阶段 1 `locked_shadow_mask`；固定 `shadow_removal_strength: 100`；禁止读取 `shadow_reference_pixels` 回写影子。
- `stage2_asset_refinement_manifest`：逐项引用阶段 1 `asset_id`，只补微表面、接缝、边缘、磨损、湿度、反射/透射、局部缺陷、颗粒和最终景深。
- `stage2_asset_expansion`：只在 `asset_addition_mask` 的空区添加第二批辅助素材，并分配新 `asset_id`；不得移动或替换阶段 1 主素材，不得覆盖原景永久锁区。

定义：

`authorized_change_mask = cleanup_removal_mask OR subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask OR outpaint_mask`

授权遮罩外的阶段 2 RGBA 必须与阶段 1 零差异；原景永久锁 mask 即使与其他 mask 冲突也优先只读。阶段 2 验收必须确认人物、人物边缘、倒影、残影、人形负空间和全部人物影子已清除，补洞透视与纹理连续，素材几何未漂移。

## 两阶段继承与停止条件

- 两份预设完整重复并规范化复用 `photographic_fidelity_contract`、`cleanup_contract`、`canvas_expansion_contract`、`geometry_contract`、`subject_perspective_lock`、`original_scene_geometry_lock`、`ground_plane_registration`、`camera_match`、`subject_light_profile`、`environment_light_plan`、`light_interaction_regions` 和 `light_match_strength`，不得写“同阶段 1”。
- 阶段 1 负责清理、完整地面覆盖、主结构、主素材、落点、尺度、灯位和影子；阶段 2 只补洞、局部增材、材质精修和背景特效。任何改变墙顶、主景片轮廓、地面单应性或主体构图的大改都必须回到阶段 1。
- 阶段 2 最终交付是无人无影精修底板。阶段 1 的透明影子层另行保留，用户需要时再手动擦回。
- 若执行器不能输出透明 RGBA 补丁/叠加层、不能按绝对坐标确定性合成，或不能验证授权遮罩外零差异，停止并报告能力不足；禁止用模型整图生成替代。
