# 请求路由、能力门与两阶段质量门

本文件先于世界观和场景设计读取。它把大合成视为“生成图层 + 宿主确定性合成”的事务，不允许用自然语言整图重绘冒充人物或底图锁定。

## 1. intent_card

先整理：`requested_world / explicit_preserves / forbidden_changes / subject_count / subject_cutout_status / reference_roles / final_canvas_request / deliverable / uncertainties`。

- 用户明确要求优先；角色资料与场景库只补有证据的空白。
- 不能确认角色设定时使用中性母题，不伪造专属纹章、剧情地点或武器。
- 参考图逐张写 `use_only / do_not_transfer`，人物、签名、水印、品牌和独特构图默认禁止迁移。

## 2. 路由边界

- 完全换世界、扩画幅、巨型建筑/生物/载具、海报级分层重构：大合成。
- 保留场馆墙顶和机位，只重铺地面与局部布景：半合成。
- 保留大部分原背景的局部修复、VFX、打光或溶图：基础 VFX skill。
- 没有可用人物抠图且宿主不能确定性回贴时，不得声明人物像素强锁；先完成抠图或改交付为非执行方案。

## 3. executor_profile 与硬能力门

两阶段逐字段相同：

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

只有人物抠图、RGBA 补丁/透明层、绝对坐标宿主合成和像素差分全部可用，才输出 `execution_status: executable`。任一能力为 false/unknown 时输出 `blocked_by_capability` 诊断与所缺步骤，不生成伪装成可执行的两阶段预设，也不退回模型整图生成人物或 stage2 成片。

## 4. pair_manifest 与阶段继承

两份 content 写相同 `pair_id`，以及：`schema_version / skill_mode: large_composite / stage_index / stage1_required_outputs / stage2_required_inputs / shared_contract_fields / runtime_hashes`。

规范化后必须一致：`executor_profile / character_worldview_card / geometry_contract / camera_calibration / subject_perspective_lock / subject_scene_scale_contract / subject_light_profile / environment_light_plan / light_match_strength / reference_roles`。运行时 hash 不可提前伪造；标为“运行时计算”，阶段 2 执行前必须解析为真实值并匹配。

## 5. 阶段事务与合成顺序

阶段 1：

1. 只在人物 alpha 外生成 `background_plate_rgba`。
2. 基于实际背景灯源生成 `shadow_layer_rgba`；人物 alpha 内为 0。
3. 宿主顺序固定为 `background → shadow → original_subject`，保证影子不污染人物像素。
4. 验收人物回贴、角度、承重点、尺度和光源后冻结 stage1 hash/masks/assets；未通过不得进入阶段 2。

阶段 2：

1. 校验 stage1 hash、画布和 mask 包。
2. 先在人物/影子移除联合 mask 内生成完整无人无影补洞。
3. 背景侧素材、材质、VFX 生成透明 RGBA layer；需要压在未来人物前方的内容延期。
4. 宿主从 stage1 副本开始按绝对坐标合成，禁止模型全画幅回写。
5. 未授权区 RGBA 零差异；失败只回滚当前 patch/layer。

背景侧纹理或 VFX 可在**已验收补洞区**自然延伸，避免出现人形负空间；必须有显式 layer mask 和完整背景逻辑，不能沿人物轮廓描边。

## 6. 人物与影子边界情况

- 多人物：每人独立 alpha、bbox、质心、承重点与 pixel hash；影子可共享但必须记录 `caster_ids`，阶段 2 全部移除。
- 坐姿/跪姿：接触面不是默认脚底，使用臀腿、膝、手或道具承重点。
- 悬空：不可见承载面时不伪造脚底接触影；只在物理可达表面生成投影，或明确 `no_contact_shadow_reason`。
- 无可见地面：影子层仍可为空，但要写证据和原因；不得为了满足字段制造漂浮黑影。

## 7. 参数作用域与 VFX 层级

- 阶段 1 的 `scene_layers` 控制主结构和第一批资产。
- 阶段 2 的 `scene_layers` 仅是只读快照；新增量改用 `stage2_overlay_layers`，不能借 richness 重画天空、建筑、道路或主资产。
- 每个 background VFX 写叙事来源、深度层、覆盖预算、主体净区、光照传播、景深/颗粒和最小重试 mask。多 VFX 共享叙事瞬间与环境因果，但各自保留真实运动方向和颜色。
- 生成 `composition_budget`：默认 1 个主视觉、2–4 个辅助素材族、最多 2 个明显自发光源；用户未要求的层可 `enabled:false/richness:0`。丰富度增加优先扩展纵深、尺度变化和材质差异，不均匀铺满五层。

## 8. 五道质量门

1. **能力门**：人物抠图、透明补丁、绝对坐标合成和差分全部可用。
2. **继承门**：共享合同、画布、灯位、人物坐标和 stage1 hash 一致。
3. **人物/世界几何门**：人物像素零差异；地平线、灭点、承重点、尺度、主资产与灯位成立。
4. **无人底板/合成门**：stage2 无人物无影、无人物形负空间；补洞、资产、材质和 VFX 的遮挡、光影、景深、颗粒正确。
5. **交付门**：两份 JSON 合法、参数 target 存在、mask 不冲突、失败可定位并回滚到最小输出层。
