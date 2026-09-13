---
name: cos-large-composite-prompt
description: >
  为 COS 人像生成可直接导入 Nano Banana/Gemini 插件的大合成两阶段 JSON 预设。
  用于完全换背景、扩画幅、海报级世界重构、巨型生物/建筑/载具和大量分层特效；阶段 1 保留原人物并根据新场景光源生成正确影子，
  阶段 2 通过局部补洞、透明素材层与宿主确定性合成移除人物及其影子；阶段 1 的影子仅作为可选独立层交给用户后期手动擦回。
  不用于局部小特效或保留大部分原背景的半合成。
---

# COS 大合成提示词

交付两份按顺序使用的插件预设：`step1_subject_shadow_composite` 与 `step2_subject_removed_refined_plate`。阶段 1 只生成背景板和独立影子层，最终人物由宿主把原始透明抠图按绝对坐标确定性回贴；阶段 2 锁定底图坐标、移除人物及其影子、补全遮挡区，增加第二批素材，把阶段 1 素材细化为最终质量并添加背景特效。

## 完整输出要求（不可省略）

- 每次在同一回答中直接输出两份完整、可导入的外层 JSON，禁止先给或只给精简版、示例版、核心提示词、字段摘要、伪代码或未转义内层对象，也不得要求用户再次追问完整版。
- 两份外层 JSON 都必须包含 `id/title/content/params/category/subCategory/refImages/_isFactory`；`content` 必须是合法单行转义 JSON，包含本技能和输出格式要求的全部内层字段、五层场景、光源档案、融入合同、质检与约束。
- 阶段 1 必须提供五层丰富度/精细度、`light_match_strength`、`contact_shadow/cast_shadow/ambient_occlusion`、`stage1_execution_contract`、`subject_lock_contract`、`base_frame_manifest` 与 `shadow_lock_package`；阶段 2 必须提供五层读取/锁定参数、`light_match_strength`、固定为 100 的 `shadow_removal_strength`、`base_frame_lock`、`stage2_execution_contract`、`shadow_removal_contract`、`material_refinement/background_vfx_intensity/background_particle_density`。每个 `target` 必须指向真实存在的内层字段。
- 禁止用占位符、省略号、“同阶段1”“同上”或解释性文字替代任何必填对象。两阶段需要复用的相机、几何和光源字段也必须在两份 `content` 中逐字段完整写出，并通过一致性校验。
- 说明文字可以简短，但不能代替预设。只有用户明确要求保存为文件时才写入磁盘；否则在回答中原样给出两份完整 JSON。

## 必读资源

1. 每次读取 [两阶段流程](references/large-composite.md)、[角色与场景决策](references/character-scene.md) 和 [输出格式](references/output-schema.md)。
2. 选场景与道具时读取 [大合成场景素材库](references/scene-library.md)；需要更全面的跨主题道具、材质、植物、生物、天气与模块化素材时再读 [综合素材库](references/asset-library.md)。
3. 加特效时读取 [华丽特效库](references/vfx-library.md)。
4. 每次都读取 [环境光源反推](references/lighting-reconstruction.md)，先冻结人物原光档案再设计新世界。

## 不可协商的锁定

- 人物身份、脸、五官、表情、妆面、肤色、发型/发丝、服装纹理、配饰、武器和道具核心像素不变。
- 人数、动作、姿态、肢体角度、视线、手势不变。
- 最终画布确定后，两阶段尺寸与比例逐像素一致。人物 X/Y、中心、头顶、脚点/承托点、宽高、旋转和占画比例零偏移。
- 参考图只提取通用环境、材质、色彩、光线与层次，不复制人物、水印、签名、品牌或独特构图。

## 工作流

1. 建立最终画布。用户未指定时根据人物原位置与叙事留白选择，但不得自动缩小人物；扩画幅只扩背景。
2. 建立 `character_worldview_card`，按 [角色与场景决策](references/character-scene.md) 选择一个主世界、一个主视觉和最多两个辅助母题。每件道具写 `worldbuilding_basis` 与置信度。
3. 建立 `geometry_contract` 与 `subject_perspective_lock`。用户未提供焦距、光圈、角度时执行视觉标定：用视野、畸变与空间压缩判断焦距范围；用焦平面厚度、主体/背景距离与散景判断光圈观感；用地平线、至少两组环境直线、地面可见量及顶/底面判断机位高度、pitch、roll、yaw 和灭点。写视觉估计、证据和置信度，不伪造 EXIF。
4. 按 [环境光源反推](references/lighting-reconstruction.md) 建立并冻结 `subject_light_profile`、`environment_light_plan` 与默认 90 的 `light_match_strength`。阶段 1 的天空、窗户、太阳、棚灯、路灯、霓虹、火焰或法阵灯位必须共同解释人物现有打光。
5. 阶段 1 固定拆成 1A 拍摄角度锁定与背景板、1B 独立影子层、1C 宿主确定性合成。先以原片地平线、机位高度、pitch/yaw/roll、人物视线高度、脚点透视、两组环境直线和身体透视缩短复原真实拍摄角度；1A 再只在人物 alpha 外生成服从该角度的场景骨架与五层基础素材；1B 以原人物作为光照/承重点参考，只输出画布同尺寸透明影子层；1C 从背景板复制开始，按原始人物 alpha 的绝对坐标逐像素回贴原人物，再叠加独立影子层。模型不得返回或采用重绘、移动、缩放后的完整人物。完成后输出 `subject_lock_contract`、`stage1_execution_contract`、`shadow_lock_package` 和 `base_frame_manifest`。
6. 阶段 2 以阶段 1 为不可变底图，禁止让生成模型返回整张最终图。固定拆成 2A 人物与影子洞局部补丁、2B 透明素材/材质/特效叠加层、2C 宿主确定性合成：2A 只写 `subject_removal_mask OR shadow_removal_mask`，2B 只写显式 addition/refinement/vfx masks 且遮罩外 alpha=0，2C 从阶段 1 原图逐像素复制开始，只在授权遮罩内合成补丁与叠加层，不回写影子。阶段 2 输出 `subject_count: 0` 且不含人物影子，阶段 1 独立影子层留给用户后期手动擦回。
7. 按 100% / 50% / 缩略图质检：阶段 1 检查拍摄角度、人物回贴像素和影子正确性，阶段 2 检查无人无影输出、补景连续、材质和特效。失败只重做对应阶段。

## 阶段 1 影子导出协议

- 阶段 1 必须输出 `hard_shadow_lock` 所需的 `locked_shadow_mask`、`shadow_reference_pixels`、遮罩布尔公式、只读编辑规则与逐像素验收，供用户后期手动擦回；阶段 2 不再保留该锁区。
- `locked_shadow_mask` 是阶段 1 接触影、环境遮蔽和投射影的画布同尺寸联合遮罩；从人物 alpha 中排除人物本体，但保留与鞋底相接的影子像素，供用户后期擦回。阶段 2 不再把该区设为只读，也不重新生成影子。
- 阶段 1 处理顺序固定为：生成背景板 → 生成透明独立影子层 → 宿主回贴原始人物 → 导出影子包。阶段 2 不得读取参考像素回写影子。
- 阶段 1 导出的独立影子层必须保留原画布坐标、RGBA、透明度和混合模式，供用户后期手动擦回。

## 阶段 1 人物绝对锁与背景板合成协议

- 阶段 1 的“保留人物”不能交给生成模型执行。模型只生成 `background_plate_rgba` 与 `shadow_layer_rgba`；人物原图是宿主的不可变输入层。
- `subject_lock_contract` 必须声明原始透明人物引用、画布绝对坐标、alpha/bbox、中心、头顶、脚点、宽高、旋转和像素哈希；`subject_transform_allowed: false`、`subject_repaint_allowed: false`、`subject_model_output_allowed: false`。
- `stage1_execution_contract` 固定为：1A 生成背景板（人物区 alpha=0 或由宿主遮挡）；1B 生成透明影子层（人物像素 alpha=0）；1C `output = copy(background_plate_rgba)`，按原始人物 alpha 逐像素回贴，再按影子绝对坐标合成。任何模型整图人物都丢弃。
- 1A/1B 的所有图层必须保持最终画布尺寸和绝对坐标，禁止自动裁切、缩放、旋转、透视变换、智能重排或按人物重新构图。
- 阶段 1 验收：回贴后人物 alpha bbox、质心、面积、脚点、姿态和 RGBA 与原始抠图逐通道一致；人物区外新增场景不允许反向覆盖人物像素。任一差异均只重做 1A/1B，不能让模型修人物。
- 阶段 1 角度验收优先于素材丰富度：地平线、灭点、人物脚点承重、视线高度和身体透视必须先通过；角度不匹配时降低素材密度并重做背景，禁止移动人物来配合场景。

## 阶段 2 底图硬锁与补丁合成协议

- 提示词里的“锁定”不是执行级像素保护。只要阶段 2 把阶段 1 平图整张交给生成模型并直接采用其整图输出，就必然允许校舍、天空、道路、月轮等区域漂移；此模式一律判定为不合格。
- 阶段 1 必须输出 `base_frame_manifest`：最终画布宽高、阶段 1 原图引用/哈希、人物移除 mask、影子锁 mask，以及允许阶段 2 新增素材、材质细化、背景特效的独立显式 mask。禁止阶段 2 自行语义重画这些 mask。
- 阶段 2 必含 `base_frame_lock` 与 `stage2_execution_contract`，其中 `global_generative_render: false`、`immutable_base_image: stage1_output`、`transform_allowed: false`、`mask_coordinates: canvas_absolute`。
- 2A 只生成 `subject_fill_patch_rgba`：尺寸与画布相同或携带绝对坐标，`subject_removal_mask` 外 alpha 必须为 0；不得返回或采用全画幅背景。
- 2B 分别生成 `asset_overlay_rgba`、`refinement_overlay_rgba`、`vfx_overlay_rgba`；每层遮罩外 alpha 必须为 0，不得含新的底色、天空、建筑、道路或全局调色。会改变主建筑、天空结构、道路轮廓或大面积基础几何的素材必须前移到阶段 1。
- 2C 必须由宿主确定性合成器执行，不允许模型执行：`output = copy(stage1_output)`；仅在 `subject_removal_mask OR shadow_removal_mask` 内覆写补洞，随后按允许 mask alpha 合成三类叠加层，不回写影子。任何层都禁止缩放、旋转、平移或自动对齐。
- 定义 `authorized_change_mask = subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask`。人物/影子移除区允许改变以生成连续背景，其余未授权区域输出与阶段 1 的 RGBA 差分必须为 0。
- 阶段 2 验收必须确认 shadow_removal_mask 内无人物影子残留；不要求也不得复制阶段 1 影子。用户后期使用阶段 1 独立影子层手动擦回。
- 若插件不能输出透明 RGBA 补丁/叠加层，或宿主不能按 mask 做确定性合成与逐像素校验，必须停止并报告“当前执行器无法保证底图与影子锁定”；禁止继续批量尝试。

## 阶段 2 去影子协议

- 阶段 2 的目标是“无人、无人物影子”的背景底板；不要把阶段 1 影子当作锁区，也不要从 `shadow_reference_pixels` 回写。
- `shadow_removal_mask` 直接读取阶段 1 `locked_shadow_mask` 的画布绝对坐标。`subject_removal_mask` 与 `shadow_removal_mask` 可以共同用于 2A 局部补洞；影子区允许被背景连续填充。
- 阶段 2 只需保证主体区与影子区无人物/人形残影、无黑色投影残留；不要求影子像素与阶段 1 相同。用户后期使用阶段 1 独立影子层手动擦回。
- `authorized_change_mask = (subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask)`；新增素材、材质和特效仍须与 `NOT (subject_removal_mask OR shadow_removal_mask)` 相交，避免把影子误当新增素材。

修改或验收光源流程时，运行 [光源测试用例](references/lighting-test-cases.json) 中的大合成与强自发光断言。

## 五层丰富度与精细度

两份预设都必须包含 `scene_layers.ground / airborne / foreground / midground / background`。每层分别提供：

- `richness` 0–100：0 关闭；1–25 单一稀疏；26–50 一个主物/素材族；51–75 一主加 1–2 辅；76–90 华丽多层；91–100 极盛但保留人物识别区和负空间。
- `detail_precision` 0–100：1–25 类别/颜色/大形；26–50 加尺度/朝向/基础材质；51–75 加接缝/粗糙度/边缘/磨损/透反射；76–90 加微表面/工艺/年代/分区反射；91–100 英雄资产级复合材质与微小几何。

默认 richness：ground 70、airborne 65、foreground 55、midground 75、background 70；默认 detail_precision 75。高精细度不代表远景和前景同样锐利，最终可见度必须服从景深与空气透视。

每个启用层包含 `depth_zone`、`richness`、`detail_precision`、`elements`、`perspective_contract`、`scale_contract`、`focus_blur_contract`、`lighting_and_shadow`、`occlusion`。每个元素包含世界观依据、人物尺度参照、落点/朝向/可见面、材质微表面、同深度锐度上限和物理影子。

### 素材丰富程度定义

- `material_richness` 不是“画面越满越好”，而是四项的综合：独立素材族数量、同族实例数量、前/中/远/空中深度覆盖、以及材质/形态/使用痕迹的变化；每项都必须服从人物识别区、透视、景深和负空间。
- 0–20：仅保留必要主资产，单一素材族，大片留白；用于构图或角度测试。
- 21–40：主资产加 1 个辅助族，每个深度区 1–3 个实例，材质只做基础区分。
- 41–60：主资产加 2–3 个辅助族，至少覆盖地面、中景、远景三层，同族实例有尺寸/朝向变化。
- 61–80：主资产加 4–6 个辅助族，五层均有明确角色，补充接缝、磨损、反射、透射和遮挡变化，但保留清晰识别区。
- 81–100：英雄级丰富度；多族、多实例、多深度和复合材质同时成立，仅在空区充足且不会改变主场景轮廓时使用。超过 90 必须逐项列出新增素材，禁止均匀撒点或全局换景。
- 阶段 1 的丰富度优先用于主结构、承托、透视和光影稳定；阶段 2 的丰富度只用于授权空区的第二批局部素材、材质细化和透明特效层。任何改变天空、建筑、道路或主轮廓的“丰富度”必须前移到阶段 1。

## 透视、比例与虚化硬规则

- 人物身高=1.0，用头宽、肩宽、手掌与脚长交叉校准地砖、台阶、家具、门、建筑、武器、载具和巨兽。同深度至少比较两个场景参照物，禁止巨型地砖、微缩建筑或玩具道具。
- 先锁定人物眼睛/面部或原片主焦平面。foreground、midground、background 按与焦平面的距离渐进改变轮廓扩散、微对比、锐度和高光散景；不能整层统一高斯模糊。
- airborne 与特效拆为近/中/远三组。贴地法阵远端随地面景深变软；穿过人物前后的火、雾、雷、粒子分别服从遮挡和虚化；静止建筑不能用模糊掩盖错误透视。
- 每个特效输出 `anti_sticker_contract` 与 `anti_sticker_validation`，用体积/厚度、前后穿插、边缘衰减、局部人物染色、投影/反射、介质/接触反应及颗粒匹配消除贴图感；任一关键项缺失即拒绝。
- 远景仍需结构和灭点正确，只降低可见高频细节、对比和饱和；近景不套远雾。

## 光影与成像

- 阶段 1 明确主光、辅光、自发光、环境色和雾深度；影子生成模型只输出透明影子层，人物本体由原始抠图回贴。阶段 2 移除人物本体及影子，最终是否擦回影子由用户后期决定。
- 两阶段都包含 `subject_light_profile`、`environment_light_plan`、`light_interaction_regions`、`light_consistency_validation`、`light_match_strength`；前三项中的光源身份、位置、方向、颜色、软硬和强度比逐字段相同。
- 阶段 1 的所有承重点有短而深的接触影；投射影从阶段 1 实际背景光源反推，并按光源方向、高度、尺寸、颜色、人物姿态、遮挡和表面起伏生成。阶段 2 必须先提取这些影子的差分区域并锁定。
- 阶段 2 不得保留或回写阶段 1 影子；必须清理接触影、环境遮蔽和投射影，且不得留下黑色人形残影。阶段 1 影子只作为独立图层交给用户后期擦回。
- 阶段 1 负责场景骨架与第一批基础素材，确保透视、尺度、接地、灯位和影子已稳定；阶段 2 不得推翻这些基础。
- 阶段 2 的 `stage2_asset_expansion` 可以在空区增加第二批辅助道具、植物、结构附件和空间层次素材，但不得替换或移动阶段 1 主资产，也不得进入人物/影子移除区。
- 阶段 2 的材质精修覆盖阶段 1 与阶段 2 素材，增强粗糙度、缝隙、微表面、反射、透射、潮湿、磨损和颗粒；背景特效最后执行，且必须有深度、遮挡、焦外、颗粒和光影反馈。
- 最后匹配同深度亮度、黑位、白平衡、局部锐度、RGB 颗粒、压缩与色深。

## 交付命名

- 阶段 1：`f_scene_<slug>-step1-subject-shadow-composite`，category `scene`；最终合成图人物数量等于输入实际人数，但人物像素必须来自宿主原始抠图回贴。
- 阶段 2：`f_scene_<slug>-step2-subject-removed-refined-plate`，category `scene`，人物数量 0，不含阶段 1 影子；影子由用户后期从阶段 1 独立层擦回。
- 两个 content 都是合法、单行、转义后的内层 JSON；不得含注释、占位符或省略号。
- 两份 params 都提供 `light_match_strength`（0–100、默认 90、target 同名），只控制环境贴合原光的严格度。
