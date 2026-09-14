#!/usr/bin/env python3
"""Validate a semi/large COS composite preset pair with stdlib only."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODE = "semi_composite" if "semi" in ROOT.name else "large_composite"
LAYER_NAMES = ("ground", "foreground", "midground", "background", "airborne")

OUTER_REQUIRED = {
    "id", "title", "content", "params", "category", "subCategory", "refImages", "_isFactory",
}
COMMON_REQUIRED = {
    "role_instruction", "intent_card", "executor_profile", "execution_status", "pair_id",
    "pair_manifest", "runtime_bindings", "geometry_contract", "camera_calibration",
    "subject_perspective_lock", "subject_scene_scale_contract", "scene_layers",
    "subject_light_profile", "environment_light_plan", "light_interaction_regions",
    "light_consistency_validation", "light_match_strength", "integration", "validation",
    "constraints", "subject_count",
}
SEMI_REQUIRED = {
    "photographic_fidelity_contract", "cleanup_contract", "canvas_expansion_contract",
    "original_scene_geometry_lock", "ground_plane_registration", "retained_original_scene",
    "camera_match",
}
LARGE_REQUIRED = {"character_worldview_card", "composition_budget", "vfx_stage_assignment"}
STAGE1_REQUIRED = {
    "subject_lock_contract", "stage1_execution_contract", "shadow_controls",
    "base_frame_manifest", "shadow_lock_package",
}
STAGE2_REQUIRED = {
    "base_frame_lock", "stage2_execution_contract", "shadow_removal_contract",
    "stage2_overlay_layers", "stage2_asset_expansion", "background_refinement",
    "background_vfx", "final_assembly_manifest",
}
SEMI_STAGE2_REQUIRED = {"background_only_contract", "stage2_asset_refinement_manifest"}
SHARED_FIELDS = {
    "executor_profile", "geometry_contract", "camera_calibration", "subject_perspective_lock",
    "subject_scene_scale_contract", "subject_light_profile", "environment_light_plan",
    "light_match_strength", "reference_roles",
}
SEMI_SHARED_FIELDS = {
    "photographic_fidelity_contract", "cleanup_contract", "canvas_expansion_contract",
    "original_scene_geometry_lock", "ground_plane_registration", "retained_original_scene",
    "camera_match",
}
CAPABILITY_TRUE = {
    "subject_cutout_available", "rgba_patch_output", "absolute_coordinate_composite",
    "pixel_diff_validation", "multi_turn_support",
}
COMPOSITE_ORDER = [
    "background_plate_rgba", "shadow_layer_rgba", "original_subjects",
    "subject_relight_overlay_rgba", "foreground_occluder_rgba",
]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list)):
        return bool(value)
    return value is not None


def resolve_target(root: Any, path: str) -> list[Any]:
    values = [root]
    for raw in path.split("."):
        array = raw.endswith("[]")
        key = raw[:-2] if array else raw
        next_values: list[Any] = []
        for value in values:
            if not isinstance(value, dict) or key not in value:
                continue
            child = value[key]
            if array:
                if isinstance(child, list):
                    next_values.extend(child)
            else:
                next_values.append(child)
        values = next_values
    return values


def load_preset(path: Path, stage: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    label = f"stage{stage}"
    try:
        outer = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, None, [f"{label} 外层 JSON 无法解析：{exc}"], warnings
    if not isinstance(outer, dict):
        return None, None, [f"{label} 外层必须是 object"], warnings
    missing = sorted(OUTER_REQUIRED - outer.keys())
    if missing:
        errors.append(f"{label} 缺少外层键：{', '.join(missing)}")
    suffix = "step1-subject-shadow-composite" if stage == 1 else "step2-subject-removed-refined-plate"
    preset_id = outer.get("id")
    if not isinstance(preset_id, str) or not re.fullmatch(rf"f_scene_[a-z0-9]+(?:-[a-z0-9]+)*-{suffix}", preset_id):
        errors.append(f"{label}.id 命名非法")
    if outer.get("category") != "scene":
        errors.append(f"{label}.category 必须是 scene")
    if outer.get("_isFactory") is not True:
        errors.append(f"{label}._isFactory 必须为 true")
    for key in ("title", "subCategory"):
        if not isinstance(outer.get(key), str) or not outer[key].strip():
            errors.append(f"{label}.{key} 必须是非空字符串")
    if not isinstance(outer.get("refImages"), list):
        errors.append(f"{label}.refImages 必须是 array")
    if not isinstance(outer.get("params"), list):
        errors.append(f"{label}.params 必须是 array")

    raw = outer.get("content")
    if not isinstance(raw, str):
        return outer, None, errors + [f"{label}.content 必须是 JSON 字符串"], warnings
    if "\n" in raw or "\r" in raw:
        errors.append(f"{label}.content 必须是单行字符串")
    if re.search(r"(?:\.\.\.|…|\bTODO\b|\bTBD\b|同阶段\s*1|同上)", raw, re.IGNORECASE):
        errors.append(f"{label}.content 含占位符或省略引用")
    try:
        content = json.loads(raw)
    except json.JSONDecodeError as exc:
        return outer, None, errors + [f"{label}.content 反序列化失败：{exc}"], warnings
    if not isinstance(content, dict):
        return outer, None, errors + [f"{label}.content 内层必须是 object"], warnings
    if not content or next(iter(content)) != "role_instruction":
        errors.append(f"{label}.role_instruction 必须是内层第一个键")

    required = COMMON_REQUIRED | (SEMI_REQUIRED if MODE == "semi_composite" else LARGE_REQUIRED)
    required |= STAGE1_REQUIRED if stage == 1 else STAGE2_REQUIRED
    if MODE == "semi_composite" and stage == 2:
        required |= SEMI_STAGE2_REQUIRED
    missing = sorted(required - content.keys())
    if missing:
        errors.append(f"{label} 缺少内层键：{', '.join(missing)}")

    for key in required - {"runtime_bindings"}:
        if key in content and not nonempty(content[key]):
            errors.append(f"{label}.{key} 不得为空")
    if not isinstance(content.get("intent_card"), dict):
        errors.append(f"{label}.intent_card 必须是 object")
    if not isinstance(content.get("runtime_bindings"), list):
        errors.append(f"{label}.runtime_bindings 必须是 array")
    else:
        for index, binding in enumerate(content["runtime_bindings"]):
            if not isinstance(binding, dict) or not {"binding", "type", "resolver", "required_before_stage"} <= binding.keys():
                errors.append(f"{label}.runtime_bindings[{index}] 字段不完整")

    profile = content.get("executor_profile")
    if not isinstance(profile, dict):
        errors.append(f"{label}.executor_profile 必须是 object")
    else:
        if profile.get("mask_support") != "explicit":
            errors.append(f"{label}.executor_profile.mask_support 必须是 explicit")
        for key in CAPABILITY_TRUE:
            if profile.get(key) is not True:
                errors.append(f"{label}.executor_profile.{key} 必须为 true")
        if profile.get("lock_reliability") != "strong":
            errors.append(f"{label}.executor_profile.lock_reliability 必须是 strong")
        if outer.get("refImages") and profile.get("multi_reference_support") != "supported":
            errors.append(f"{label} 有参考图时 multi_reference_support 必须是 supported")
    if content.get("execution_status") != "executable":
        errors.append(f"{label}.execution_status 必须是 executable")

    manifest = content.get("pair_manifest")
    if not isinstance(manifest, dict):
        errors.append(f"{label}.pair_manifest 必须是 object")
    else:
        if manifest.get("skill_mode") != MODE:
            errors.append(f"{label}.pair_manifest.skill_mode 必须是 {MODE}")
        if manifest.get("stage_index") != stage:
            errors.append(f"{label}.pair_manifest.stage_index 必须是 {stage}")
        for key in ("schema_version", "stage1_required_outputs", "stage2_required_inputs", "shared_contract_fields", "runtime_hashes"):
            if not nonempty(manifest.get(key)):
                errors.append(f"{label}.pair_manifest.{key} 不得为空")

    if not isinstance(content.get("subject_count"), int) or isinstance(content.get("subject_count"), bool):
        errors.append(f"{label}.subject_count 必须是整数")
    elif stage == 1 and content["subject_count"] < 1:
        errors.append("stage1.subject_count 必须至少为 1")
    elif stage == 2 and content["subject_count"] != 0:
        errors.append("stage2.subject_count 必须为 0")

    layers = content.get("scene_layers")
    validate_layers(layers, f"{label}.scene_layers", errors)
    if stage == 2:
        validate_layers(content.get("stage2_overlay_layers"), f"{label}.stage2_overlay_layers", errors)

    constraints = content.get("constraints")
    if not isinstance(constraints, dict) or not isinstance(constraints.get("must_not"), list) or not constraints.get("must_not"):
        errors.append(f"{label}.constraints.must_not 必须是非空 array")
    strength = content.get("light_match_strength")
    if not is_number(strength) or not 0 <= strength <= 100:
        errors.append(f"{label}.light_match_strength 必须在 0–100")

    validate_params(outer.get("params"), content, stage, errors, warnings)
    if stage == 1:
        validate_stage1(content, errors)
    else:
        validate_stage2(content, errors)
    return outer, content, errors, warnings


def validate_layers(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} 必须是 object")
        return
    for name in LAYER_NAMES:
        layer = value.get(name)
        if not isinstance(layer, dict):
            errors.append(f"{label}.{name} 必须是 object")
            continue
        if not isinstance(layer.get("enabled"), bool):
            errors.append(f"{label}.{name}.enabled 必须是 boolean")
        for field in ("richness", "detail_precision"):
            number = layer.get(field)
            if not is_number(number) or not 0 <= number <= 100:
                errors.append(f"{label}.{name}.{field} 必须在 0–100")


def validate_params(params: Any, content: dict[str, Any], stage: int, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(params, list):
        return
    seen: set[str] = set()
    for index, param in enumerate(params):
        label = f"stage{stage}.params[{index}]"
        if not isinstance(param, dict) or not {"key", "label", "type", "default", "target"} <= param.keys():
            errors.append(f"{label} 字段不完整")
            continue
        key = param.get("key")
        if not isinstance(key, str) or not key:
            errors.append(f"{label}.key 必须是非空字符串")
        elif key in seen:
            errors.append(f"{label}.key 重复：{key}")
        else:
            seen.add(key)
        target = param.get("target")
        values = resolve_target(content, target) if isinstance(target, str) else []
        if not values:
            errors.append(f"{label}.target 不存在：{target}")
            continue
        if stage == 2 and isinstance(target, str) and target.startswith("scene_layers."):
            errors.append(f"{label} 不得修改阶段 2 的只读 scene_layers")
        if param.get("type") == "number":
            numeric_fields = (param.get("min"), param.get("max"), param.get("default"), param.get("step"))
            if not all(is_number(value) for value in numeric_fields):
                errors.append(f"{label} 的 min/max/default/step 必须是数值")
            else:
                minimum, maximum, default, step_value = numeric_fields
                if minimum > maximum or not minimum <= default <= maximum or step_value <= 0:
                    errors.append(f"{label} 的数值范围非法")
                if any(not is_number(value) or not minimum <= value <= maximum for value in values):
                    errors.append(f"{label}.target 数值超出范围")
                if any(value != default for value in values):
                    warnings.append(f"{label}.default 与 target 当前值不一致")
        elif param.get("type") == "select":
            options = param.get("options")
            if not isinstance(options, list) or param.get("default") not in options:
                errors.append(f"{label}.options/default 非法")
        else:
            errors.append(f"{label}.type 必须是 number 或 select")


def validate_stage1(content: dict[str, Any], errors: list[str]) -> None:
    lock = content.get("subject_lock_contract")
    subjects = lock.get("subjects") if isinstance(lock, dict) else None
    if not isinstance(subjects, list) or not subjects:
        errors.append("stage1.subject_lock_contract.subjects 必须是非空 array")
    else:
        if content.get("subject_count") != len(subjects):
            errors.append("stage1.subject_count 必须等于 subjects[] 长度")
        ids: set[str] = set()
        required = {"subject_id", "source", "alpha", "bbox", "centroid", "contact_points", "pixel_hash", "occlusion_order"}
        for index, subject in enumerate(subjects):
            if not isinstance(subject, dict) or not required <= subject.keys():
                errors.append(f"stage1.subjects[{index}] 字段不完整")
                continue
            if subject.get("subject_id") in ids:
                errors.append(f"stage1.subjects[{index}].subject_id 重复")
            ids.add(subject.get("subject_id"))
        if not nonempty(lock.get("union_subject_alpha")):
            errors.append("stage1.subject_lock_contract.union_subject_alpha 不得为空")
        for key in ("subject_transform_allowed", "subject_repaint_allowed", "subject_model_output_allowed"):
            if lock.get(key) is not False:
                errors.append(f"stage1.subject_lock_contract.{key} 必须为 false")
    execution = content.get("stage1_execution_contract")
    if not isinstance(execution, dict) or execution.get("composite_order") != COMPOSITE_ORDER:
        errors.append("stage1.stage1_execution_contract.composite_order 非法")
    shadow = content.get("shadow_lock_package")
    if not isinstance(shadow, dict) or shadow.get("shadow_mode") not in {"generated", "none"}:
        errors.append("stage1.shadow_lock_package.shadow_mode 必须是 generated 或 none")
    elif shadow["shadow_mode"] == "generated":
        for key in ("locked_shadow_mask", "shadow_reference_pixels", "export_shadow_layer", "caster_ids"):
            if not nonempty(shadow.get(key)):
                errors.append(f"stage1.shadow_lock_package.{key} 不得为空")
    elif not nonempty(shadow.get("no_shadow_reason")):
        errors.append("shadow_mode=none 时必须提供 no_shadow_reason")
    manifest = content.get("base_frame_manifest")
    required_manifest = {
        "stage1_output_hash", "canvas_size", "subject_removal_mask", "locked_shadow_mask",
        "asset_addition_mask", "material_refinement_mask", "background_vfx_mask",
    }
    if MODE == "semi_composite":
        required_manifest |= {"visible_retained_scene_lock", "occluded_reconstruction_mask", "outpaint_mask"}
    if not isinstance(manifest, dict) or not required_manifest <= manifest.keys():
        errors.append("stage1.base_frame_manifest 字段不完整")


def validate_stage2(content: dict[str, Any], errors: list[str]) -> None:
    base = content.get("base_frame_lock")
    if not isinstance(base, dict):
        errors.append("stage2.base_frame_lock 必须是 object")
    else:
        if base.get("immutable_base_image") != "stage1_output":
            errors.append("stage2.base_frame_lock.immutable_base_image 必须是 stage1_output")
        if base.get("global_generative_render") is not False or base.get("transform_allowed") is not False:
            errors.append("stage2.base_frame_lock 必须禁止整图生成和几何变换")
        if base.get("mask_coordinates") != "canvas_absolute":
            errors.append("stage2.base_frame_lock.mask_coordinates 必须是 canvas_absolute")
    shadow = content.get("shadow_removal_contract")
    if not isinstance(shadow, dict):
        errors.append("stage2.shadow_removal_contract 必须是 object")
    else:
        if shadow.get("shadow_removal_strength") != 100:
            errors.append("stage2.shadow_removal_contract.shadow_removal_strength 必须为 100")
        if shadow.get("source_mask") != "locked_shadow_mask from stage1":
            errors.append("stage2.shadow_removal_contract.source_mask 非法")
        if shadow.get("no_restore") is not True:
            errors.append("stage2.shadow_removal_contract.no_restore 必须为 true")
    execution = content.get("stage2_execution_contract")
    if not isinstance(execution, dict):
        errors.append("stage2.stage2_execution_contract 必须是 object")
    else:
        mask = str(execution.get("authorized_change_mask", ""))
        for required_mask in ("subject_removal_mask", "shadow_removal_mask"):
            if required_mask not in mask:
                errors.append(f"stage2.authorized_change_mask 缺少 {required_mask}")
        if execution.get("reject_full_frame_model_output") is not True:
            errors.append("stage2 必须拒绝模型全画幅输出")
    assembly = content.get("final_assembly_manifest")
    if not isinstance(assembly, dict) or assembly.get("layer_order") != COMPOSITE_ORDER:
        errors.append("stage2.final_assembly_manifest.layer_order 非法")


def validate_pair(step1_path: Path, step2_path: Path) -> tuple[list[str], list[str]]:
    outer1, content1, errors1, warnings1 = load_preset(step1_path, 1)
    outer2, content2, errors2, warnings2 = load_preset(step2_path, 2)
    errors = errors1 + errors2
    warnings = warnings1 + warnings2
    if not outer1 or not outer2 or not content1 or not content2:
        return errors, warnings
    if outer1.get("subCategory") != outer2.get("subCategory"):
        errors.append("两阶段 subCategory 必须一致")
    if outer1.get("refImages") != outer2.get("refImages"):
        errors.append("两阶段 refImages 必须一致")
    if content1.get("pair_id") != content2.get("pair_id") or not nonempty(content1.get("pair_id")):
        errors.append("两阶段 pair_id 必须相同且非空")
    shared = SHARED_FIELDS | (SEMI_SHARED_FIELDS if MODE == "semi_composite" else {"character_worldview_card"})
    for field in sorted(shared):
        if content1.get(field) != content2.get(field):
            errors.append(f"两阶段共享字段不一致：{field}")
    layers1, layers2 = content1.get("scene_layers"), content2.get("scene_layers")
    if isinstance(layers1, dict) and isinstance(layers2, dict):
        for layer in LAYER_NAMES:
            if layers1.get(layer) != layers2.get(layer):
                errors.append(f"两阶段 scene_layers.{layer} 快照不一致")
    return errors, warnings


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        print("用法：python validate_pair.py <step1.json> <step2.json>", file=sys.stderr)
        return 2
    errors, warnings = validate_pair(Path(sys.argv[1]), Path(sys.argv[2]))
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"验证失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"验证通过：{MODE} 两阶段一致，0 个错误，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
