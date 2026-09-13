# 模块注册表（规范键名）

本表是模块键名的唯一事实来源。生成预设只写规范键；括号中的旧名只用于理解旧预设，不再输出。

风险分用于选择 `single_pass` 或 `ordered_micro_passes`，不是效果强度。

## A 清理与技术修复

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `cleanup_plan` | 去路人、器材、杂物并按邻域补洞 | 1 |
| `remove_overlay` | 去自有/获授权水印、日期、角标 | 1 |
| `wardrobe_malfunction_fix` | 修复打底裤/安全裤等服装边缘穿帮，保持覆盖 | 2 |
| `capture_artifact_fix` | 摩尔纹、色边、传感器灰点、条带、JPEG 块、轻微鬼影 | 1 |
| `enhance_plan` | 去噪、去模糊、恢复已有发丝/织纹/金属细节 | 1 |
| `hand_fix` | 手指数量、关节与握持修复 | 2 |
| `foot_fix` | 脚趾、鞋边、落地接触与鞋跟结构修复 | 2 |
| `hair_fix` | 补断发、发缝、毛躁与局部发量 | 2 |
| `wig_lace_fix` | 隐藏蕾丝边、胶痕、发网和不自然发际衔接 | 1 |
| `armor_prop_repair` | 修复盔甲 EVA 接缝、掉漆、翘边、道具裂缝与比例 | 2 |
| `glass_reflection_fix` | 去除隔窗/展柜拍摄产生的大面积反射并恢复原场景 | 2 |
| `lens_geometry_fix` | 修正桶形/枕形畸变、垂直线倾斜与轻微透视歪斜 | 2 |
| `low_light_rescue` | 暗光提质、彩噪与色块抑制、暗部细节恢复 | 2 |
| `highlight_shadow_recovery` | 恢复可救的高光与阴影层次，不虚构烧毁细节 | 1 |

## B 人像与妆面

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `face_retouch` | 保身份修瑕疵、黑眼圈与 ≤10% 轮廓微调 | 3 |
| `makeup_refine` | 眼线、睫毛、眉形、腮红、唇妆与舞台妆对称性 | 2 |
| `body_sculpt` | 小幅液化与体态，必须修复背景形变 | 3 |
| `body_finish` | 皮肤光泽、微汗、水珠与真实毛孔 | 2 |
| `skin_unify` | 脸颈与露肤区肤色统一 | 1 |
| `eye_color` | 仅虹膜换色；发光瞳术归 `vfx_plan` | 1 |
| `teeth_nail` | 牙齿/眼白轻修与美甲（旧 `teeth_whiten`、`nail`） | 1 |
| `glasses_glare_fix` | 压制遮眼反光，保留镜片、镜框与合理环境反射 | 1 |
| `expression_refine` | 显式要求时微调嘴角、眉眼张力或疲态，保身份 | 3 |
| `gaze_direction_fix` | 显式要求时小幅校正双眼视线与汇聚点 | 3 |
| `jewelry_fix` | 修复耳饰、项链、胸针、珠串、反光与佩戴连接 | 1 |

## C 服装、鞋袜与风动

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `hosiery_fix` | 丝袜织纹、丝光、破损、改色与花纹 | 2 |
| `outfit_plan` | 服装去污去皱、材质增强与改色（旧 `outfit_refresh`） | 2 |
| `hair_flow_plan` | 发梢与可动布料统一风向（旧 `wind_flow`） | 2 |
| `costume_fit_fix` | 修复领口、腰封、袖口、裙摆和甲片的贴合与褶皱 | 2 |
| `support_rig_cleanup` | 去除胶带、别针、鱼线、夹子、透明肩带等拍摄支撑 | 1 |
| `transparent_material_fix` | 修复薄纱、PVC、欧根纱、透明翼与半透明配件 | 2 |
| `material_texture_enhance_plan` | 分材质增强皮肤、发丝、织物、皮革、金属、宝石、透明件与毛绒质感 | 2 |

## D 增材、角色特征与物理落地

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `prop_plan` | fufu、公仔、小动物、头饰、武器与手持物 | 2 |
| `add_race_feature` | 兽耳、尾巴、精灵耳、犄角、獠牙 | 2 |
| `battle_damage` | 战损、血迹、伤痕、绷带、污渍与做旧 | 2 |
| `add_skin_mark` | 纹身、咒印、泪痣、雀斑等曲面贴合 | 1 |
| `shadow_plan` | 新增/校正接触影、投影与悬浮影子 | 2 |
| `reflection_plan` | 地面、水面、镜面倒影 | 2 |
| `foreground_plan` | 花枝、纱、玻璃、烟雾等前景框景 | 1 |
| `clone_plan` | 实体分身同框，不同于半透明残影 | 3 |
| `levitate_plan` | 整体悬浮并重建承托、影子和气流线索 | 3 |
| `subject_harmonize_plan` | 统一新增主体/道具与原场景的颜色、照明、阴影和颗粒 | 2 |
| `image_blend_plan` | 把供体图的指定内容局部溶入底图，并控制蒙版与融合方式 | 3 |

## E 特效

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `vfx_plan` | 元素、魔法、天气、科技、战斗与抽象能量特效 | 2–3 |
| `lens_fx_plan` | 有来源的 bloom、眩光、星芒、棱镜、色散、镜头水滴 | 1–2 |

## F 光影与色彩

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `lighting_reshape` | 可解释的补光、轮廓光和明暗重塑 | 2 |
| `virtual_lighting_plan` | 新增可定位的主光、辅光、轮廓光、投影光纹或实景光源 | 2–3 |
| `background_tone` | 仅背景压暗、祛灰、降杂色 | 1 |
| `grading_plan` | 人物与背景统一的整体影调与色彩 | 2 |
| `color_match` | 参考图追色，只迁移色彩/影调不搬内容 | 2 |
| `blur_plan` | 背景景深、追焦、径向或方向动态模糊 | 2 |
| `depth_atmosphere_plan` | 按深度添加雾化、空气透视与远景对比衰减 | 2 |

## G 画布与场景局部

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `sky_plan` | 仅替换天空（旧 `sky_replace`） | 2 |
| `outpaint_plan` | 仅扩展原画框之外像素 | 3 |

## H 成片包装

| 规范键 | 用途 | 风险 |
|---|---|---:|
| `poster_plan` | 电影 KV、杂志封面、角色卡、双重曝光 | 2 |
| `frame_plan` | 拍立得、相纸、胶片格、黑白边 | 1 |
| `text_plan` | 明确文案的标题、署名、日期与层级排版 | 3 |
| `stylize_plan` | 二次元、厚涂、工笔、油画、BJD、潮玩等介质转换 | 3 |

共 58 个规范模块。库中没有的新需求可新增临时模块，但必须遵循五段式、锁定合同和授权规则；若会长期复用，再补入本表和对应模块库。
