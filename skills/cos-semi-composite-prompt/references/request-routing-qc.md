# 请求路由、能力门与两阶段质量门

本文件先于场景设计读取。目标是确认任务确实属于半合成，并在写两份预设前阻止不可执行的图层、遮罩或宿主能力承诺。

## 1. intent_card

先整理：`requested_changes / explicit_preserves / forbidden_changes / retained_venue_regions / cleanup_keep_whitelist / reference_roles / canvas_request / deliverable / uncertainties`。

- 用户明确要求优先；场景库只补不会改变主题与锁定范围的空白。
- 没有图片时不编造人数、坐标、墙顶边界、灯位、EXIF 或遮挡关系，写运行时检测。
- 参考图逐张写 `use_only` 与 `do_not_transfer`，不得迁移人物、作者标识、品牌、水印或独特构图。

## 2. 路由边界

- 保留场馆远墙、天花板、钢架、主机位，只在地面/空区/边缘加入主题布景：半合成。
- 大部分原背景保留，只做局部特效、清理、打光或小道具：基础 VFX skill。
- 场馆结构不再保留，背景成为完整新世界或需要重摆人物：大合成。
- 仅需普通调色精修参数、不需要插件 JSON：clean-retouch。

## 3. executor_profile 与硬能力门

两阶段内都写并保持一致：

```json
{
  "target_family": "nano_banana_or_gemini_image_edit",
  "subject_cutout_available": true,
  "mask_support": "explicit",
  "rgba_patch_output": true,
  "absolute_coordinate_composite": true,
  "pixel_diff_validation": true,
  "multi_reference_support": "supported | unsupported | unknown",
  "multi_turn_support": true,
  "lock_reliability": "strong"
}
```

只有 `subject_cutout_available=true`、`mask_support=explicit` 且 `rgba_patch_output + absolute_coordinate_composite + pixel_diff_validation` 全为 true 时，两份预设才可标记 `execution_status: executable`。任一能力为 false/unknown 时停止生成“可执行预设”，改为 `execution_status: blocked_by_capability` 的诊断，列出缺失能力和宿主分层合成方案；禁止退回模型整图重绘。使用参考图时还必须确认多参考能力。

## 4. pair_manifest 与继承

两份 content 都写相同 `pair_id` 与 `pair_manifest`：

- `schema_version`
- `skill_mode: semi_composite`
- `stage_index: 1 | 2`
- `stage1_required_outputs`
- `stage2_required_inputs`
- `shared_contract_fields`
- `runtime_hashes`（画布、人物 RGBA、stage1 底图、mask 包；未知时写运行时计算，不伪造）

下列对象规范化后必须完全相同：`executor_profile / photographic_fidelity_contract / canvas_expansion_contract / geometry_contract / camera_calibration / subject_perspective_lock / original_scene_geometry_lock / ground_plane_registration / subject_scene_scale_contract / subject_light_profile / environment_light_plan / light_match_strength / reference_roles`。

图片分析后仍需由宿主提供的坐标/hash 使用正式 `runtime_bindings[]`，每项写 `binding/type/resolver/required_before_stage`；它是可解析的外部输入合同，不是 `TODO`、省略号或自然语言占位符。

## 5. 遮罩分区

半合成必须区分：

- `visible_retained_scene_lock`：输入中真实可见且要保留的墙、顶、钢架等像素；阶段 1/2 均只读。
- `occluded_reconstruction_mask`：原本被人物、影子、路人或器材遮住的墙地部分；这些像素并不存在于输入中，允许按邻域几何和材质补全。
- `editable_scene_mask`：允许新增主题布景的空区。
- `outpaint_mask`：仅原画框外。

扩图时必须写 `original_to_final_translation_px=[left_expansion_px, top_expansion_px]`；原图、人物 alpha、影子与锁区只做同一个整数像素平移，不重新归一化、缩放或插值。

不得把完整语义“墙面”都设为永久像素锁；否则人物后方墙面无法补洞。若显式 mask 意外重叠，先修 mask，不用优先级强行覆盖。

## 6. 阶段事务

阶段 1：

1. `1A_cleanup_patch`：只清路人/器材 mask。
2. `1B_background_plate`：合成清理 patch 与五层基础素材。
3. `1C_shadow_layer`：输出透明影子层，人物 alpha 内严格为 0。
4. `1D_host_composite`：`background → shadow → original_subject → subject_relight_overlay → foreground_occluder`。后两层仅在任务需要时输出；人物源 RGBA 始终零差异。
5. 通过后冻结 stage1 hash 与全部 mask；未通过不得进入阶段 2。

阶段 2：

1. 校验 stage1 hash、画布和 mask 包。
2. 生成并验收人物/影子补洞 patch。
3. 再生成局部素材、材质和背景 VFX 透明层。
4. 宿主按绝对坐标确定性合成。
5. 未授权区做 RGBA 差分；失败只回滚当前 patch/layer。

阶段 2 背景侧素材可以在**已验收的补洞区**连续延伸，但必须由显式 layer mask 控制，并证明不形成沿人物轮廓排列的人形负空间。需要改变人物局部光色的内容输出 `subject_relight_overlay_rgba`，需要压在最终人物前方的内容输出 `foreground_occluder_rgba`；二者进入 `final_assembly_manifest`，不得烘焙进人物源层或无人背景板。

## 7. 参数作用域

- 阶段 1 的 `scene_layers.*.richness/detail_precision` 只设计主结构和第一批素材。
- 阶段 2 的 `scene_layers` 是只读快照，不再挂 richness 滑块。
- 阶段 2 新增量使用 `stage2_overlay_layers.*.richness/detail_precision`，不得重新规划墙顶、主地面、主景片或 stage1 asset。
- 每个 param 的 `target` 必须存在、类型/范围正确；影子移除固定 100。

## 8. 五道质量门

1. **能力门**：补丁、透明层、绝对坐标合成与差分能力已确认。
2. **继承门**：两阶段共享合同一致，stage2 输入 hash 与 stage1 输出一致。
3. **人物/几何门**：阶段 1 回贴人物 RGBA 零差异；墙顶、机位、地面平面和尺度未漂移。
4. **补洞/合成门**：阶段 2 无人物无影，补洞连续；素材边缘、遮挡、光影、景深和颗粒匹配。
5. **交付门**：两份外层/内层 JSON 合法、参数可解析、遮罩无冲突、失败能回滚到最小输出层。
