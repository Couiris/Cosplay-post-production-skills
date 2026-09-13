# 大合成两阶段流程

大合成分两次处理：第一次拆成背景板、独立影子层和宿主人物回贴，借助可见人物参考获得准确承重和投影，但禁止模型输出人物；第二次只让模型生成局部补洞与透明叠加层，最终由宿主基于阶段 1 不可变底图确定性合成。两次均禁止自动重构画布或人物变换。

## 触发条件

满足任一项即启用：

- 完整替换背景并保留人物抠图
- 海报级场景重构或跨画幅扩图
- 新增大量道具、建筑、载具、大型生物或复杂前中后景
- 用户说“大合成”“先保留人物生成影子”“去人留影”或“无人底板”

普通局部特效、简单调色、修脸、服装修复和保留原背景的轻量半合成不走本流程。

## 共同前提

1. 在图像编辑软件中先建立最终尺寸和比例的画布。
2. 把原始透明人物抠图放到最终位置；从此不再改变画布尺寸和人物变换参数。
3. 记录人物图层的 X/Y、宽高、中心点、脚点和旋转角度。两阶段始终沿用同一组值。
4. 若模型或插件会自动按比例重裁，先关闭该功能；提示词中的比例只用于校验，不用于再次改画幅。
5. 用户未给焦距、光圈和拍摄角度时，从原图视觉估计：焦距用视野、畸变、线条收敛和空间压缩；光圈用焦平面厚度、前后景距离和散景；角度用地平线、至少两组环境线、地面可见量和物体顶/底面。记录范围、证据和置信度，不编造 EXIF。
6. 建立角色世界观卡；每件道具必须说明与时代、地域、组织、职业、能力体系或剧情时刻的关系。
7. 读取 [环境光源反推](lighting-reconstruction.md)，从人物原图建立 `subject_light_profile`，据此冻结 `environment_light_plan` 与默认 90 的 `light_match_strength`；两阶段不得重新估计或漂移。

## 阶段 1：保留人物的场景影子合成

### 输入

- 已是最终尺寸的画布
- 放在最终坐标的原始透明人物抠图，阶段 1 必须保留其核心像素
- 场景或海报参考图（如有）

### 输出目标

输出与最终画布逐像素同尺寸的完整合成图。模型只生成 `background_plate_rgba` 和透明 `shadow_layer_rgba`；人物 alpha 内的人物由宿主从原始透明抠图逐像素回贴，禁止模型重绘人物。阶段 1 只在 alpha 外生成场景骨架与五层第一批基础素材，并依据实际光源在承载面上生成完整的接触影、环境遮蔽和投射影。阶段 1 必须稳定主要建筑、道路、承托、关键道具、植物、远景地标、透视、尺度、景深、灯位与基础材质；最终高密度辅助素材、英雄级材质细化和主要特效留给阶段 2。

阶段 1 同时必须输出 `shadow_lock_package`：画布同尺寸的 `locked_shadow_mask`、锁区 `shadow_reference_pixels`、接触影/环境遮蔽/投射影三个分区、透明独立影子层及其画布坐标。还必须输出 `base_frame_manifest`：阶段 1 原图引用/哈希、尺寸、人物移除遮罩及阶段 2 各类授权修改遮罩。两者都是阶段 2 的强制输入；只有合成图而没有锁包和 manifest 时，阶段 1 不算完成。

### 必备 content 模块

```json
{
  "task": "只生成背景板和独立影子层，由宿主按原始alpha绝对坐标回贴人物",
  "input_requirement": {
    "canvas_lock": "输出宽高与输入完全相同，不裁切、不扩图、不缩放",
    "subject_guide": "读取人物alpha、姿态、厚度、承重点与遮挡；alpha内核心像素不可编辑"
  },
  "generation_mode": {
    "mode": "background_plate_plus_shadow_layer",
    "subject_count": 1,
    "subject_rendering": "模型禁止输出人物像素；宿主只接受原始透明抠图",
    "preserve_subject": "由宿主按原始alpha、绝对坐标、尺寸、姿态和道具逐像素回贴",
    "shadow_generation": "按阶段1实际背景光源生成透明独立影子层，不含人物像素"
  },
  "shadow_controls": {
    "contact_shadow": 60,
    "cast_shadow": 50,
    "ambient_occlusion": 50
  },
  "shadow_lock_package": {
    "required": true,
    "locked_shadow_mask": "阶段1三类影子的画布同尺寸联合遮罩",
    "shadow_reference_pixels": "锁区原始RGBA像素引用",
    "shadow_regions": ["contact_shadow", "ambient_occlusion", "cast_shadow"],
    "exclude_subject_pixels": true,
    "export_shadow_layer": "透明背景独立影子层，保持原画布坐标"
  }
}
```

阶段 1 还必须包含以下执行合同：

```json
{
  "subject_lock_contract": {
    "source": "original_transparent_subject_cutout",
    "subject_transform_allowed": false,
    "subject_repaint_allowed": false,
    "subject_model_output_allowed": false,
    "lock_values": "运行时记录alpha bbox、质心、头顶、脚点、宽高、旋转和RGBA哈希",
    "composite_rule": "host pastes original subject pixels at canvas_absolute coordinates"
  },
  "stage1_execution_contract": {
    "pass_1a_background_plate": "模型只输出background_plate_rgba；人物区alpha=0或由宿主遮挡",
    "pass_1b_shadow_layer": "模型只输出shadow_layer_rgba；人物像素alpha=0，影子使用画布绝对坐标",
    "pass_1c_deterministic_composite": "宿主从copy(background_plate_rgba)开始，先按原始alpha回贴人物，再按绝对坐标合成shadow_layer_rgba",
    "reject_full_frame_subject": true,
    "reject_any_subject_transform": true,
    "validation": "回贴后人物bbox、质心、面积、脚点和RGBA与原始抠图逐通道零差异"
  }
}
```

上例 `subject_count: 1` 仅表示单人输入；实际预设必须写入检测到的真实整数人数。

### 构图规则

- 背景、道具和大型元素围绕人物当前 alpha 和坐标自适应，不移动人物。
- 阶段 1 的首要优先级是复原原片拍摄角度：先锁定机位高度、俯仰 pitch、水平 yaw、roll、地平线、人物视线高度、脚点透视和建筑线灭点，再生成背景；背景必须服从人物角度，不能让人物迁就背景。
- 至少用地平线、两组环境直线、地面可见量、人物脚点接触和身体透视缩短五类证据交叉验证拍摄角度；证据冲突时降低背景复杂度并重做背景，不得改变人物。
- 阶段 1 不需要生成人物后方被完全遮挡的背景纹理；该区域由阶段 2 擦除人物时补全。
- 狐狸眼睛、招牌、道具主体等关键视觉信息避开人物参考框；允许被人物遮挡的部分要符合真实前后关系。
- 五层分别记录 0–100 的 richness 与 detail_precision。ground/foreground/midground/background/airborne 的数量与细节独立控制，不能靠一个总华丽度替代。
- 先锁定人物主焦平面；前景、中景、远景、空中素材和特效按真实深度渐进虚化。同一特效跨越前后景时内部渐变，不能整层统一模糊或全部锐利。
- 用人物身高、头宽、肩宽、手掌和脚长校准地砖、台阶、家具、建筑、载具和巨兽，同深度至少比较两个场景参照物。
- 天空、窗、太阳、棚灯、路灯、霓虹、火焰、法阵与体积光必须按冻结的 `subject_light_profile` 落位，使环境受光面、背光面、反射与投影共同解释人物原光。

### 严禁项

- 严禁重绘、替换、复制、删除或改变原人物；严禁新增第二人物。
- 严禁改变画布尺寸、比例或边界。
- 严禁人物 alpha 内出现纯色色块、模糊补丁、人脸重绘或发光轮廓。

### 预设命名

- `id`: `f_<category>_<slug>-step1-subject-shadow-composite`
- `title`: `阶段1-<主题>保留人物场景影子合成`
- `category`: 通常为 `background` 或 `scene`

## 阶段 2：硬锁影子、去人补景、增补素材、细化材质与添加特效

### 输入

- 阶段 1 输出的“保留人物+完整场景+正确影子”合成图
- 原始人物 alpha 和锁定变换，用于精确擦除人物本体，不得扩大到已生成的影子区
- 与阶段 1 逐像素同尺寸的画布；阶段 2 输出仍不得出现人物

### 输出与编辑区域

- 阶段 2 禁止全画幅生成式重绘；生成模型只允许返回补丁或透明 RGBA 叠加层，最终成片只能由宿主确定性合成器生成。
- `base_frame_lock`：以阶段 1 原图为不可变底图，禁止缩放、裁切、旋转、平移、自动对齐、全局重绘与全局调色。

- `subject_removal_mask`：以原始 alpha 为核心，只在消除发丝污染所需的窄带内扩展；不得包含接触影和投射影。
- `shadow_removal_mask`：直接读取阶段 1 的 `locked_shadow_mask`，作为允许清除阶段 1 影子的区域；不得重新语义识别或移动该区域。
- 遮罩公式固定为 `subject_removal_mask = cleaned_subject_alpha`、`shadow_removal_mask = locked_shadow_mask`；2A 补景遮罩为两者联合，素材/材质/特效遮罩必须排除两者。
- 输出必须是“补全后的无人无影背景 + 第二批新增素材 + 全部素材最终材质精修 + 背景空间特效”，`subject_count: 0`。禁止人物本体、边缘、倒影、残影、人形负空间或阶段 1 影子残留。

阶段 2 原样复用阶段 1 的 `subject_light_profile`、`environment_light_plan` 和 `light_match_strength`。它从阶段 1 读取人物 alpha 与影子差分区域：人物 alpha 和影子差分都是待移除区。阶段 2 不重新设计或保留影子；若需要影子，用户后期从阶段 1 独立影子层擦回。

### 必备 content 模块

```json
{
  "task": "移除阶段1人物本体及其影子，补全连续无人无影背景并进行材质和特效精修",
  "subject_removed_refined_plate": {
    "subject_count": 0,
    "subject_removal_mask": "以阶段1原人物alpha为核心移除人物，只为清理发丝色边扩展必要窄带",
    "fill_behind_subject": "按周围场景几何、透视、材质、光照和景深连续补全人物后方背景",
    "shadow_removal_mask": "直接读取阶段1 locked_shadow_mask，清除接触影、环境遮蔽和投射影，不回写参考像素",
    "final_manual_overlay": "用户之后可在后期软件中把原始透明人物按记录坐标1:1覆盖，并按需从阶段1独立影子层擦回"
  },
  "shadow_removal_contract": {
    "shadow_removal_strength": 100,
    "source_mask": "locked_shadow_mask from stage1",
    "remove": "阶段1接触影、环境遮蔽和投射影全部清除",
    "mask_boolean": "shadow_removal_mask = locked_shadow_mask",
    "no_restore": true,
    "manual_restore_policy": "用户后期按需从阶段1独立影子层擦回",
    "validation": "shadow_removal_mask内不得残留可识别人物影子或黑色人形投影"
  },
  "base_frame_lock": {
    "immutable_base_image": "stage1_output",
    "global_generative_render": false,
    "transform_allowed": false,
    "mask_coordinates": "canvas_absolute"
  },
  "stage2_execution_contract": {
    "pass_2a_subject_fill": "只生成subject_fill_patch_rgba，(subject_removal_mask OR shadow_removal_mask)外alpha=0",
    "pass_2b_overlays": "分别生成asset/refinement/vfx透明RGBA层，各层在对应允许遮罩外alpha=0",
    "pass_2c_deterministic_composite": "宿主从copy(stage1_output)开始，仅按遮罩合成补丁和叠加层，不回写影子锁区",
    "authorized_change_mask": "subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask",
    "unchanged_region_mask": "NOT authorized_change_mask",
    "reject_full_frame_model_output": true
  },
  "background_refinement": {
    "material_refinement": 75,
    "allowed": "精修已定型表面的粗糙度、缝隙、微表面、磨损、潮湿、反射、透射、颗粒和局部色阶",
    "locked": "不改道具种类、场景几何、尺度、坐标、灯位和景深"
  },
  "stage2_asset_expansion": {
    "asset_expansion_intensity": 65,
    "allowed": "在人物alpha、识别净区和locked_shadow_mask之外增加第二批辅助道具、植物、结构附件和空间层次素材",
    "locked": "不替换、不移动、不缩放阶段1主资产，不改变相机、灭点、地面、灯位、景深和影子",
    "integration": "每件新增素材具有世界观依据、真实尺度、落点、遮挡、材质、景深、受光和投影"
  },
  "background_vfx": {
    "background_vfx_intensity": 55,
    "background_particle_density": 50,
    "placement": "只在人物后方、承载面或人物alpha之外增加有深度、遮挡和光影反馈的特效",
    "forbidden": "不进入人物alpha，不贴着alpha边缘排列，不形成人形负空间"
  },
  "deferred_foreground_vfx": {
    "policy": "需要压在最终人物前方的特效不烘焙进本阶段，记录后留待单独合成"
  }
}
```

### 阶段 1 拍摄角度与影子生成

- 阶段 1 从其实际生成的背景识别主光、填充光和次级光源，与冻结 `environment_light_plan` 交叉验证后生成影子。
- 阶段 1 的影子模型只能输出透明独立影子层；人物本体不随影子层生成或变形。人物最终位置由原始抠图回贴结果决定。
- 可见窗、太阳、顶灯、自发光物、反射高光和背景已有投影必须共同解释人物影子；不得只依赖文字计划而忽略实际生成背景。
- 背景光源与冻结计划冲突时，拒绝生成影子并重做阶段 1，不得通过移动影子或新增隐藏灯位掩盖冲突。
- 接触阴影必须出现在脚底、坐姿臀腿接触面、支撑手掌或道具落地点；没有接触关系的位置不凭空加黑边。
- 硬光产生边缘较清楚的投射影；大面积柔光产生低对比、宽羽化影；彩色环境光允许阴影带轻微互补色，但不能纯黑。
- 人物悬空或地面不可见时，不伪造脚底影；只在实际邻近表面生成能够由背景光源解释的投影或环境遮蔽。
- 阶段 2 直接读取阶段 1 影子差分区作为 `shadow_removal_mask` 并清除影子；不得保留、重新检测、重新生成或回写影子。
- 阶段 2 验收只检查影子移除区无残留，不检查与阶段 1影子的 RGBA 相同；阶段 1 独立影子层由用户后期按需擦回。

### 阶段 2 固定执行顺序

1. 校验阶段 1 原图哈希、画布尺寸、绝对坐标 masks 与影子锁包；不匹配则停止。
2. 2A 仅在 `subject_removal_mask` 内生成补洞 patch；遮罩外 alpha=0。
3. 2B 仅在显式 `asset_addition_mask`、`material_refinement_mask`、`background_vfx_mask` 内生成透明叠加层；不得返回新的整张底图。
4. 2C 宿主执行 `output = copy(stage1_output)`，按遮罩依次合成补洞、素材、材质和特效层，不做任何几何变换。
5. 不回写 `shadow_reference_pixels`，不覆盖独立影子层；该层交给用户后期处理。
6. 校验 `subject_removal_mask OR shadow_removal_mask` 内无人无影，且 `unchanged_region_mask` 的 RGBA 差分为 0；否则丢弃阶段 2 输出。

### 背景材质精修与特效

- 阶段 1 只负责场景骨架和第一批基础素材。它必须让所有主要结构与光影关系成立，但不承担最终素材密度和华丽特效。
- 阶段 2 必须先执行 `stage2_asset_expansion`：在空区增加第二批辅助道具、植物、结构附件和空间层次素材。新增素材不得进入人物 alpha、识别净区或 `locked_shadow_mask`，不得移动、替换或缩放阶段 1 主资产。
- 阶段 2 随后执行 `background_refinement`：对阶段 1 与阶段 2 的全部素材精修缝隙、粗糙度、微表面、制造痕迹、磨损、潮湿、反射、透射、颗粒与局部色阶；不得改变已定型几何、坐标、灯位或景深。
- 阶段 2 必须包含 `background_vfx`：根据用户主题在背景侧增加雾、烟、尘、花瓣、火星、雨雪、光尘或体积光中的适配元素，并与阶段 1 光源和介质互动。特效只能位于人物后方、承载面或人物 alpha 之外；不得在 alpha 内补纹理，也不得贴着 alpha 边缘排列成轮廓。
- 需要压在最终人物前方的花瓣、烟雾或能量不烘焙进阶段 2；将其记入 `deferred_foreground_vfx`，供最终覆盖人物后单独生成或合成。
- 新特效需通过深度拆分、遮挡、边缘衰减、景深、运动模糊、颗粒、接触/介质反应、投影/反射检查；禁止贴图感。

### 素材丰富程度定义

`material_richness` 由独立素材族数量、同族实例数量、深度覆盖和材质/形态变化四项共同决定，不等于无差别堆满画面：

- 0–20：仅有必要主资产，单一素材族，大片留白；用于构图和拍摄角度验证。
- 21–40：主资产加 1 个辅助族，每个深度区 1–3 个实例，只有基础材质区分。
- 41–60：主资产加 2–3 个辅助族，覆盖地面、中景、远景三层，同族实例有尺寸/朝向变化。
- 61–80：4–6 个辅助族，五层均有明确角色，并有接缝、磨损、反射、透射和遮挡变化，同时保留人物识别区。
- 81–100：英雄级多族、多实例、多深度、复合材质；仅在空区充足且不改变主轮廓时使用，超过 90 必须逐项列出素材，禁止均匀撒点或全局换景。

阶段 1 将丰富度优先分配给主结构、承托、透视和光影稳定；阶段 2 只在授权空区增加局部第二批素材、材质变化和透明特效。会改变天空、建筑、道路或主轮廓的素材必须在阶段 1 完成。

### 严禁项

- 严禁在输出中出现人物本体、人物边缘、发丝、服装、第二人物、替身、人物倒影、人物剪影、人物残影或人形光圈。
- 严禁把隐藏参考人物复制、重绘、半透明化或烘焙进背景。
- 严禁统一黑色外发光式假阴影、与光源反向的影子、漂浮影子或穿过不连续表面的影子；阶段2不得新增或保留人物影子。
- 严禁忽略阶段 1 实际背景光源，或生成与窗、太阳、灯具、反射和已有环境投影冲突的影子。
- 严禁采用模型输出的阶段 1 人物作为成片；严禁对原始人物抠图做任何缩放、裁切、旋转、透视变换、重绘或自动对齐。
- 严禁把阶段 2 模型返回的全画幅图直接作为成片；严禁在授权遮罩外改变阶段 1 的天空、建筑、道路、树木、道具、灯位、色调、颗粒或像素。

### 预设参数

第一阶段至少提供：

- `contact_shadow`：接触阴影强度，默认 60
- `cast_shadow`：投射阴影强度，默认 50
- `ambient_occlusion`：环境遮蔽强度，默认 50

第二阶段至少提供：

- `shadow_removal_strength`：阶段 1 影子移除强度，默认 100
- `asset_expansion_intensity`：阶段 2 新增素材强度，默认 65
- `material_refinement`：背景材质精修强度，默认 75
- `background_vfx_intensity`：背景空间特效强度，默认 55
- `background_particle_density`：背景粒子密度，默认 50

### 预设命名

- `id`: `f_<category>_<slug>-step2-subject-removed-refined-plate`
- `title`: `阶段2-<主题>去人留影精修特效板`
- `category`: `scene`

## 交付与校验

大合成请求必须同时交付两份预设文件，并明确使用顺序。

阶段 1 校验：输出尺寸等于输入；人物数量等于输入实际人数；宿主回贴后人物 alpha bbox、质心、面积、脚点、坐标、姿态和 RGBA 与原始抠图逐通道一致；背景板和影子层不含人物像素；新场景光源与独立影子层一致。

阶段 2 校验：输出人物数量为 0且不含阶段1影子；人物及影子移除区背景连续；`unchanged_region_mask` 的 RGBA 差分为 0；不存在人物本体、边缘、倒影、残影或人形负空间；材质和特效精修不改授权遮罩外几何、灯位、底色或像素。

两阶段光源校验：对 `subject_light_profile`、`environment_light_plan` 和 `light_match_strength` 做规范化序列化后必须完全相同；`light_consistency_validation` 必须拒绝灯位漂移、无来源色温、阴影软硬冲突、遮挡表面受光和全身染色。
