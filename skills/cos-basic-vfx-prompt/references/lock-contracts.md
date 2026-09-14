# 人物与背景锁定合同（单阶段特效版）

每次生成都必须读取。本文件把两个合成技能的锁定思想压缩成适合“保留原主体和大部分原场景的增量后期”版本。锁定是提示目标与验收条件，不是生成模型的物理保证；可靠性取决于执行器是否支持显式蒙版、图层和原人物回贴。

## 0. 单阶段授权制（与两阶段合成的根本区别）

- 两阶段合成会重造大面积场景；本 skill 只允许在明确授权区内修复、增材或叠加效果。默认输出一个预设；复杂请求可以在同一预设内用 `pass_plan` 表达有序微步骤。
- 「锁定」在提示词层面不是物理保护，因此必须用三重手段把模型的自由度压到最低：
  1. **声明式硬锁**：四份合同逐字段写明什么不许动；
  2. **区域授权**：每个模块声明 `authorized_area`，特效另写 `vfx_zone / depth_order`，并求并集得到 `authorized_change_mask`；
  3. **执行路径约束**：禁止全画幅生成式重绘、禁止全局调色滤镜；插件支持局部重绘/蒙版时只刷授权区，发光层后期用「变亮/滤色」混合。
- 若有显式蒙版/宿主回贴，`lock_reliability=strong`，可用像素差分验收遮罩外区域；若只能整图自然语言编辑，`lock_reliability=best_effort`，要求可见一致并提示局部蒙版或回贴路径，不写“保证逐像素不变”。

## 1. subject_lock_contract（人物锁定合同）

```json
{
  "subject_lock_contract": {
    "subject_count": "输入照片中的真实人数，原样返回，不增不减",
    "identity_lock": "身份、脸型、五官、表情、妆面、瞳色、肤色基准不变",
    "hair_lock": "默认锁定发型、发色、发量、发丝轮廓与走向；只开放已启用头发模块明确列出的 allowed_delta",
    "outfit_lock": "默认锁定服装、配饰、武器与手持道具；只开放已启用服装/道具/溶图模块明确列出的 allowed_delta",
    "pose_lock": "动作、姿态、肢体角度、手势、视线、人物间相对位置不变；不补肢、不换手、不制造重复人物",
    "transform_lock": {
      "xy_position": "不变",
      "center": "不变",
      "crown_and_feet": "头顶点、脚点/承托点不变",
      "width_height": "宽高不变",
      "rotation": "旋转角不变",
      "frame_ratio": "占画面比例不变",
      "tolerance": 0
    },
    "subject_core_readonly": "授权区外为 true；授权区内仍只允许 module_allowed_deltas",
    "subject_repaint_allowed": "默认 false；仅对应人物模块的最小授权区为 true",
    "subject_transform_allowed": false,
    "subject_duplicate_allowed": false,
    "module_allowed_deltas": "根据实际启用模块动态编译：修脸只开放皮肤/妆面，换装只开放指定服装区，暗光救片只开放技术影调与噪点，虚拟灯只开放逐灯可达面，VFX 只开放 vfx_zone 与 vfx_relight_mask",
    "relight_exception": "仅 lighting_reshape 授权区、virtual_lighting_plan 逐灯 affected_surfaces、或 vfx_relight_mask 内允许模块所述光照变化；身份与几何仍锁定"
  }
}
```

要点：

- 人物 alpha 内部默认**只读**。特效从人物身后穿过、沿武器流动、在掌心生成时，交界只允许「光色叠加」，不允许重画皮肤、布料、五官。
- 翅膀、竖阵、护盾等「贴着人物长」的特效，根部锚点写清楚（肩胛、脚点、掌心、武器端点），但锚点是**特效的根**，不是修改人物的许可。
- 多人合影逐人锁定；特效不得把 A 的光错误地染到被遮挡的 B 身上。

## 2. background_lock_contract（原背景锁定合同）

提炼自合成技能的 `photographic_fidelity_contract`。本技能允许已启用模块在各自最小授权区内清理、补洞或有限扩边；除此之外背景保持只读。

```json
{
  "background_lock_contract": {
    "source_basis": "original_photo_only",
    "composition_lock": "原背景的地平线、灭点、墙地顶结构、物件位置与前后遮挡不变",
    "material_lock": "背景材质、纹理方向、接缝、粗糙度、磨损、污渍、反射、颗粒保持原样，不替换成新材质",
    "tone_color_lock": "默认锁定；仅 grading/background_tone/color_match/lighting/low_light 等已启用模块的 allowed_delta 可改变",
    "capture_lock": "默认锁定；仅 capture_artifact/enhance/low_light/capture_match/output_finish 等已启用模块的 allowed_delta 可改变",
    "no_global_grading": "默认 true；用户明确要求且启用 grading_plan/color_match/lighting_reshape 时按模块授权改为 false",
    "no_global_filter": "禁止全局柔光、全局雾、全局暗角、全局胶片颗粒、全局LUT式调色",
    "background_replace_allowed": false,
    "object_remove_allowed": false,
    "edit_allowed_only_in": "authorization_contract.authorized_change_mask（全部已启用模块 authorized_area 的并集，不仅是 vfx_zone）",
    "outside_mask_validation": "显式蒙版或宿主合成时检查 RGBA 零差异；语义蒙版时检查可见一致并标 best_effort"
  }
}
```

要点：

- 四份合同不是静态“什么都不许改”，而是先默认锁定，再把**本次实际启用模块**的 `authorized_area + allowed_delta` 编译成最小例外。未启用模块绝不能借用其他模块的授权。

- 特效对背景唯一允许的改变是「特效本身的像素」以及特效发光在邻近表面**物理可达**的反射/染色（写进对应特效的 relight_and_blend），且随距离衰减、被遮挡即终止。
- 不允许借加特效之名重新渲染背景（如「顺便把背景虚化/把墙换成城堡/把地面打湿一大片」）；这类需求转半合成/大合成技能。
- 地面法阵、冰霜蔓延、积水、裂地等贴地效果只覆盖授权的局部地面，覆盖区内允许叠加特效层，但要透出原地面纹理走向、服从原地面透视，边缘自然衰减，不能是一块圆形贴片。

## 3. geometry_camera_lock_contract（几何与相机锁定合同）

```json
{
  "geometry_camera_lock": {
    "canvas_lock": "输出分辨率、宽高比、画框与输入一致；不裁切、不缩放、不旋转、不扩画幅、不重新构图",
    "viewpoint_lock": "机位高度、俯仰pitch、偏航yaw、横滚roll、视线高度不变",
    "perspective_lock": "地平线、灭点方向、环境直线收敛关系不变",
    "lens_lock": "焦段观感、畸变、边缘拉伸不变（无EXIF时做视觉估计并标注以原片为准）",
    "depth_lock": "焦平面位置、景深范围、前后景虚化程度不变；新增特效按所在深度匹配同等虚化",
    "ground_plane": "贴地特效复用原地面平面：近宽远窄单应性、远端随景深变软",
    "scale_contract": "以人物身高=1.0、头宽/肩宽/手掌/脚长交叉校准特效尺度；翅膀、法阵、传送门等与人物比例合理，不出现尺寸离谱的特效",
    "perspective_validation_reject": [
      "特效地平线与原片冲突",
      "贴地法阵不随地面透视形变",
      "竖立体无朝向无厚度像纸片",
      "近景比远景还淡还小",
      "特效尺度与人物比例失调"
    ]
  }
}
```

焦段观感视觉估计（无 EXIF 时，仅供描述景深匹配，不写死参数）：广角全身约 24–35mm 观感、标准约 40–60mm、中长焦半身约 85–135mm；新增特效锐度不得高于同一深度的原内容。

## 4. subject_light_profile（精简版冻结光源档案）

完整方法论见 [特效材质与光影](material-light.md)。基础特效只需冻结以下字段，再让特效发光去「解释并补充」原光，而不是反转它：

```json
{
  "subject_light_profile": {
    "primary_light": {"direction": "从眼神光/鼻影/下颌影交叉判断", "elevation": "low/mid/high", "softness": "hard/semi-soft/soft", "color": "冷暖与色偏视觉估计", "confidence": "high/medium/low"},
    "rim_or_fill_light": "发丝/肩线轮廓光与暗部填充，没有证据就留空",
    "existing_shadow": {"direction": "原投影反方向", "edge": "软硬", "note": "特效投影必须服从同一方向"},
    "environment_emitters": "画面里真实可见的灯、窗、屏幕、霓虹、火焰（最高优先级证据）",
    "light_match_strength": 90
  }
}
```

铁律：**让新增特效光解释人物现有明暗，而不是重画人物去迁就特效。** 特效位置与原主光冲突时，降低发光、改为非发光形态或移动特效位置，不反转主光、不做无来源补光。

## 5. authorization_contract（全部模块授权书）

每个启用模块一份，模块授权区求并集；`vfx_plan` 内再按 effect 细分：

```json
{
  "authorization_contract": {
    "per_module": {
      "vfx_plan": {
        "authorized_area": "全部 effect.authorized_area 的并集",
        "allowed_delta": "只增加指定特效及其 vfx_relight_mask 内的物理响应",
        "edge_policy": "保留人物遮挡和真实轮廓光"
      }
    },
    "authorized_change_mask": "全部启用模块 authorized_area 的并集",
    "unchanged_region_mask": "NOT authorized_change_mask（人物核心区与未授权背景在此掩码内，只读）",
    "mask_enforcement": "explicit_mask | semantic_mask | host_composite",
    "lock_reliability": "strong | best_effort",
    "face_clean_zone": "人物面部识别区默认不进入任何 vfx_zone，粒子/光尘绕开，保持干净负空间"
  }
}
```

深度层级的默认规则：

- `behind_subject`（默认）：法阵、翅膀、传送门、护盾后弧、背景侧火焰、竖立体——从人物身后生成，被人物身体遮挡的部分必须藏到人物轮廓之后。
- `around_subject`：掌心/手中能量、沿手臂或武器爬的电流符文、周身环绕粒子——贴着人物但只在轮廓外与可达表面发光，不进入五官。
- `in_front_of_subject`：前景飘雪/花瓣/雨滴、镜头眩光、穿过人物前方的雾带——必须带景深虚化与半透明，轻擦而过，不糊脸、不改写人物像素。

## 6. execution_contract（单阶段执行合同）

```json
{
  "execution_contract": {
    "mode": "follow execution_strategy: single_pass | ordered_micro_passes | checkpointed_multi_turn",
    "base_image": "输入原照片作为唯一内容与几何基准",
    "global_generative_render": false,
    "full_frame_repaint_allowed": false,
    "transform_allowed": false,
    "global_grading_allowed": "默认 false；仅显式启用 grading_plan/color_match/lighting_reshape 时在其授权范围为 true",
    "mask_coordinates": "canvas_absolute",
    "render_rule": "只在 authorized_change_mask 内增量编辑；显式蒙版/宿主合成时 unchanged_region_mask 逐像素保留，语义蒙版时以可见一致为目标",
    "layering_order": "先背景侧特效 → 再环绕/附着特效 → 最后前穿越层；同层按 depth_order 合成",
    "local_mask_workflow": "若插件支持局部重绘/涂抹蒙版：只刷 vfx_zone，选区略大于特效边缘以获得自然衰减，人物与背景不刷",
    "glow_blend_tip": "纯发光/高光类特效可单独生成一层，后期用变亮/滤色(Screen)混合模式叠加，只保留生成的高光、排除生成的阴影，最大限度保留原片细节",
    "variation_tip": "同一预设建议生成 3–5 版，选物理交互（光染、遮挡、反射、衣料贴合）最自然的一版",
    "reject": [
      "模型整图重绘后人物五官/姿态/位置漂移",
      "授权区外背景材质或色调被改动",
      "特效与人物无任何光交互像剪贴画",
      "出现第二个人物、重复肢体、乱码文字、水印"
    ]
  }
}
```

## 7. 验收（生成后逐项核对）

1. 100% 视图：人物五官、妆面、发型、服装、手势、姿态与输入重合；无重绘、无多肢、无第二人。
2. 100% 视图：授权区外背景逐像素未变——没有被顺手虚化、改色、提亮、换材质、加暗角。
3. 50% 视图：特效透视、尺度、遮挡正确；贴地效果随地面形变；竖立体有厚度与朝向。
4. 缩略图：第一眼主体仍是人物，特效没有在亮度/饱和上喧宾夺主；脸周围干净。
5. 光影：每个自发光特效在人物/环境上有与强度相称、方向正确、随距离衰减且被遮挡终止的染色或反射；原投影方向未被推翻。
6. 景深颗粒：特效按所在深度虚化，边缘与颗粒匹配原片，无统一外发光描边、无高清贴片悬浮感。
7. 任一项失败只重做对应特效区域，不允许通过全局调色、加雾、压暗来掩盖问题。

## 8. 各功能模块的授权区与锁定例外

基础后期包含多类模块，每个模块只能在自己的授权区改动；模块之间冲突时按第 9 节优先级处理。

| 模块 | 授权区（可改） | 仍然只读（不可改） |
|---|---|---|
| cleanup_plan 清背景 | 被移除对象的 mask，补洞像素延续相邻原材质/光影/透视 | 人物、未遮挡背景、整体色调 |
| capture_artifact_fix 伪影 | 摩尔纹、色边、灰点、条带、压缩块等伪影区 | 真实纹理、真实灯光色散、构图色调 |
| remove_overlay 去水印 | 水印/文字本身+1~2px | 其余全部；仅处理用户自有/有权图 |
| wardrobe_malfunction_fix 去打底裤穿帮 | 仅服装轮廓线外露出的安全裤/衬裤边缘那一条 | **身体覆盖范围只增不减、禁生成裸露**；腿型、裙摆形态、其余服装背景 |
| enhance_plan 清晰度 | 全图做去模糊/降噪/细节增强，但只增强已有细节 | 不得新增原图没有的内容、不得磨皮美颜、不得改构图色调 |
| hand_fix 修手 | 指定手+手腕羽化区 | 手臂姿态、手上配饰道具、脸与身体其余部分 |
| foot_fix 修脚 | 指定脚/鞋+紧邻接触区 | 腿部姿态、鞋款装饰、脚点与其余地面 |
| hair_fix 补发丝 | 头发区域内（顺原毛流补断层/发缝/发量） | 发型长度造型轮廓、发色基准、脸周净区 |
| wig_lace_fix 蕾丝 | 发际线蕾丝/胶痕/发网及紧邻过渡 | 五官结构、额头比例、发型轮廓 |
| armor_prop_repair 盔甲道具 | 指定部件表面、接缝与连接处 | 角色设计、道具尺度、握持与人物姿态 |
| glass_reflection_fix 隔窗反光 | 被识别为反射的层或区域 | 透过玻璃的真实主体、玻璃框和非反射内容 |
| lens_geometry_fix 镜头几何 | 全图或背景几何变换区 | 人物身份、身体比例；裁切/扩边必须显式授权 |
| low_light_rescue 暗光救片 | 全图技术修复 | 夜景时间感、真实颗粒、可见光源颜色与构图 |
| highlight_shadow_recovery 高光阴影 | 指定高光/阴影区 | 全图曝光基准、完全剪切区不可虚构复杂细节 |
| edge_halo_spill_fix 边缘去色溢 | 污染轮廓及内外极窄过渡带 | 真实轮廓光、发丝/薄纱/透明件覆盖、人物几何 |
| face_retouch 修脸 | 皮肤瑕疵点、≤10% 轮廓微调区、妆容增强区、眼神光点 | 本人身份与五官相对位置、五官结构、肤色基准、背景 |
| makeup_refine 妆面 | 眼线/睫毛/眉/腮红/唇妆等既有妆面区 | 五官结构、身份、皮肤真实纹理 |
| body_sculpt 液化 | 身形轮廓小幅度推移区 | 关节解剖、左右对称、服装版型；**必须同步复原被推弯的背景直线** |
| body_finish 抹油/光泽肌 | 裸露皮肤的高光与反射（随肌肉骨点） | 体型结构、服装覆盖范围（不暴露）、原光源方向、毛孔肤质 |
| skin_unify 匀肤色 | 脸/颈/身体露肤区的颜色明暗 | 皮肤结构、妆色、立体光影 |
| eye_color 美瞳 | 双眼虹膜范围 | 眼型、瞳孔结构、眼神光、眼白眼眶 |
| glasses_glare_fix 眼镜反光 | 镜片内部 | 镜框、眼型、瞳色与合理环境反射 |
| expression_refine 表情 | 明确眉眼/嘴角微区 | 身份、年龄、五官距离和未授权面部区域 |
| gaze_direction_fix 视线 | 双眼虹膜/瞳孔微区 | 眼型、虹膜颜色、眼神光与面部其他结构 |
| jewelry_fix 饰品 | 饰品本体和连接/接触区 | 原设计、身体锚点、服装与人物姿态 |
| hosiery_fix 丝袜 | 丝袜区域内：织纹/丝光/补洞/改色/镂空 | 腿型与腿部解剖、袜口裙摆鞋边界、身体覆盖（不越界暴露） |
| hair_flow_plan 飘发 | 发丝末端、裙摆/披风/飘带等可动布料外沿 | 发型长度颜色、肢体、服装版型、其他背景 |
| lighting_reshape 光影重塑 | 全图明暗关系（方向唯一、可被环境解释） | 几何构图、物体位置、人物身份 |
| background_tone 背景压暗 | 背景区影调与饱和 | 人物主体亮度肤色、背景层次（不死黑） |
| color_match 追色 | 全图色彩倾向（影调轻、色彩重） | 本图内容与构图、肤色自然、参考图物体不搬入 |
| grading_plan 调色光影 | **唯一允许全图统一影调变化**的模块：人物与背景按同一规则一起变 | 几何/构图/身份；不得只改人物导致与背景割裂 |
| blur_plan 虚化 | 授权的背景区/追焦方向区 | 人物主体（除非用户要求整体追焦）、构图几何 |
| prop_plan 增材小物 | 小物落点及其接触区、被它遮挡的小范围背景 | 人物像素（接触边缘只允许投影/挤压，不允许改人体） |
| add_race_feature 兽耳尾角 | 新增特征本体及其生根/遮挡区 | 脸、发型本体、左右对称与数量 |
| battle_damage 战损 | 伤口/血迹/脏污/破边所在的皮肤或面料区 | 五官与解剖结构、服装得体覆盖（同去穿帮口径） |
| add_skin_mark 纹印 | 指定皮肤曲面 | 五官、身形、图案外皮肤 |
| outfit_plan 服装 | 服装区域内：色相/面料质感/杂乱褶皱 | 版型、结构、图案位置、身体轮廓、背景 |
| costume_fit_fix 服装贴合 | 指定领口/腰封/袖口/裙摆/甲片结构 | 身体覆盖、体型、版型与装饰位置 |
| support_rig_cleanup 支撑清理 | 胶带/鱼线/别针/夹子等支撑物 mask | 角色设计带子、锁链、服装结构与人物轮廓 |
| transparent_material_fix 透明材质 | 薄纱/PVC/透明翼等现有材质区 | 材质后的主体内容、几何和身份 |
| material_texture_enhance_plan 质感 | 分材质语义区 | 材质类别、几何、身份；不得全图同强度锐化 |
| reflection_plan 倒影 | 反射面（地面/水面）区域 | 人物本体、反射几何之外区域 |
| foreground_plan 前景 | 镜头与人物间的前景层（须虚化、只挡边缘） | 人物面部关键信息、主体清晰度 |
| clone_plan 分身 | 新增分身所在的空区及其投影区 | 原主体脸与姿态、固定机位逻辑 |
| levitate_plan 悬浮 | 人物整体位移+下方投影/气流区 | 身份五官、失重逻辑外的背景结构 |
| image_blend_plan 溶图 | 每张供体的迁移白名单与蒙版 | 底图人物姿态机位、供体禁止迁移内容 |
| subject_harmonize_plan 主体协调 | 新增主体、接触影与极小边缘光包裹区 | 原底图全局色调、人物身份与几何 |
| shadow_plan 影子 | 承载面上的接触影/投影区 | 原主体位置、主光方向、非承载面 |
| sky_plan 换天空 | 原天空 mask（沿建筑/树冠/发丝边缘自然抠界） | 天空以下全部；新天空光色必须解释原片光影 |
| outpaint_plan 扩图 | 仅原画框之外的 outpaint_mask | 原画框内部 1:1 锁定，不重采样不重绘 |
| vfx_plan 特效 | 每个特效的 vfx_zone 并集 | 人物核心区、未授权背景 |
| lens_fx_plan 镜头效果 | 由亮源决定的镜头光路或明确前景层 | 无光源区域、脸部识别区与主体清晰度 |
| virtual_lighting_plan 虚拟打光 | 每盏灯的可达面、投影和反射区 | 无法被该光路照到的区域、身份与几何 |
| depth_atmosphere_plan 空气透视 | 按深度划分的空气区 | 清晰主体、面部识别区与近景黑白点 |
| capture_match_plan 成像匹配 | 新增/修补区或显式授权的全图轻量匹配 | 主焦点清晰度、几何与已通过的光影关系 |
| poster_plan 海报 | 全图统一海报级影调 + 构图留白区（不改变人物姿态与位置） | 身份、五官、姿态坐标；默认不生成文字（乱码风险） |
| frame_plan 边框 | 画框外侧新增边框区 | 框内原图 1:1 |
| text_plan 文字 | 指定排版安全区 | 人物关键轮廓、未授权背景；文案逐字符锁定 |
| stylize_plan 风格化 | 全图渲染介质（需用户显式要求） | 身份可辨识、姿态、构图、位置、服装款式 |
| output_finish_plan 输出收尾 | 导出编码、尺寸与克制锐化 | 内容、构图、授权区、身份和原画框关系 |

锁定例外原则：**例外只开放该模块明确需要的那一维度**。grading 开放「色调」不开放「几何」；stylize 开放「渲染介质」不开放「身份姿态」；outpaint 开放「画框外」不开放「画框内」。任何模块都不开放人物身份与姿态坐标。

## 9. 增材小物锁定规则（prop_plan：fufu 公仔/小动物/道具/前景框景）

新增一个「实体物件」比加光效更容易穿帮，按元素骨架写全：

- `identity_reference`：fufu 公仔默认是**与角色同设定的 Q 版ふわふわ毛绒公仔**——大头小身、豆豆眼、短肢、毛绒面料、可见缝线与刺绣五官、吊牌可选；服装配色与角色一致但为公仔迷你版。用户指定其他公仔/动物/道具时按指定写。
- `geometry_and_scale`：以人物身高=1.0 校准真实尺寸（fufu 坐姿公仔约 0.18–0.25 个身高，怀抱时不超过小臂长度）；写清抱在怀里/扛肩/站脚边/放头顶/前景遮挡的落点与朝向。
- `material_surface`：毛绒写绒向、长短绒、缝线、刺绣、填充饱满度与织物漫反射；硬质道具写材质族（见 asset-library）；禁止塑料感光滑公仔。
- `contact_and_shadow`：与人体/地面接触处必须有接触影、轻微挤压形变（毛绒柔软）与承托关系；悬空必须给出理由（被手握住/被抱着）。
- `occlusion_depth`：在人物怀里时公仔前半挡住服装、后半被手臂遮挡；站脚边时落在地面透视上；前景框景物必须虚化。
- `lighting_match`：公仔受光方向、冷暖、软硬与 `subject_light_profile` 一致，毛绒边缘吃同色轮廓光；眼睛/吊牌塑料件只出小高光。
- 数量克制：默认 1 个主小物，最多再加 1–2 个点缀；不得复制出「第二个真人」，公仔不等于真人缩小。

## 10. 扩图规则（outpaint_plan 轻量版）

- 默认不扩；仅用户明确要求或留白确实不足时启用，记录 `mode: expand`、`original_frame_rect`、最终画布、四边扩展像素与 1:1 嵌入规则。
- 新增像素只在 `outpaint_mask = 最终画布 MINUS 原画框`；原画框内部除其他授权 mask 外零差异，禁止重采样、缩放、旋转、重排内部元素。
- 扩出区域沿原灭点延展线条、沿原材质延展纹理、沿原光源延展光影与颗粒；不得借扩图换背景、换机位或生成新主体。
- 扩图后再启用其他模块时，授权区坐标以最终画布为准，原画框内锁定关系不变。

## 11. 模块优先级（冲突时谁让谁）

固定优先级，低优先级不得覆盖高优先级锁定：

`subject_lock（身份/姿态/坐标，扣除显式 allowed_delta） > geometry_camera_lock（画布/机位/透视，扣除显式位移/扩图） > background_lock（原背景，扣除模块授权区） > outpaint 原画框内锁 > cleanup/technical_repair（清理与技术修复） > hand/hair/face/body（结构精修） > outfit/material_texture（服装与分材质质感） > image_blend/prop/vfx（溶图、增材与特效） > shadow/subject_harmonize/virtual_lighting（按实际需要） > conditional_edge_halo_spill（仅有污染时） > blur/depth_atmosphere > grading/poster > conditional_capture_match（仅不一致时） > frame/stylize > output_finish`

举例：特效光不得重画人脸（vfx 低于 subject_lock）；调色不得把刚补好的背景补洞区单独偏色（grading 低于 background_lock，必须全图统一）；风格化不得改变姿态坐标（stylize 最低，但仍受 subject_lock 约束）。

## 12. 实战兜底工作流（写进交付说明，提升成功率）

一线 cos 后期经验表明，单模型整图编辑最容易「脸变」，预设里同时给出兜底路径：

1. **局部蒙版优先**：插件支持涂抹/局部重绘时，只刷授权区，选区略大于特效/补洞边缘以获得自然衰减，人物与无关背景不刷。
2. **人物回贴**：高风险操作（强特效、换天、扩图、海报化）前先抠出人物备用；生成后用蒙版把原始人物按原位贴回。只有这类宿主合成路径才可声称人物区使用原像素。
3. **发光分层**：纯发光类效果单独生成一层，PS 混合模式用「变亮/滤色（Screen）」，只保留高光、排除生成的阴影，底图细节损失最小。
4. **小步迭代**：一次只做 1–2 个改动，后一轮追加时带「保持上一轮结果、脸不变」；同一预设生成 3–5 版选交互最自然的一版。
5. **最后追色**：多模块叠加后用 grading_plan 做一次统一追色/校色差，人物背景同规则，消除拼接感。
