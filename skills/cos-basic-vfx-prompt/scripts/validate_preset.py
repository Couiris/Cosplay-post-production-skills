#!/usr/bin/env python3
"""Validate a cos-basic-vfx-prompt preset using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


OUTER_REQUIRED = {
    "id",
    "title",
    "content",
    "params",
    "category",
    "subCategory",
    "refImages",
    "_isFactory",
}

INNER_REQUIRED = {
    "role_instruction",
    "task_summary",
    "photo_readout",
    "executor_profile",
    "execution_strategy",
    "priority_order",
    "subject_lock_contract",
    "geometry_camera_lock_contract",
    "background_lock_contract",
    "subject_light_profile",
    "authorization_contract",
    "integration",
    "acceptance_tests",
    "retry_policy",
    "constraints",
    "negative_prompt",
}

CATEGORIES = {
    "vfx", "cleanup", "enhance", "retouch", "hair", "grading", "blur",
    "prop", "outfit", "sky", "outpaint", "poster", "frame", "stylize", "combo",
}

MODULES = {
    "cleanup_plan", "remove_overlay", "wardrobe_malfunction_fix",
    "capture_artifact_fix", "enhance_plan", "hand_fix", "foot_fix", "hair_fix",
    "wig_lace_fix", "armor_prop_repair", "glass_reflection_fix", "lens_geometry_fix",
    "low_light_rescue", "highlight_shadow_recovery", "face_retouch", "makeup_refine",
    "body_sculpt", "body_finish", "skin_unify", "eye_color", "teeth_nail",
    "glasses_glare_fix", "expression_refine", "gaze_direction_fix", "jewelry_fix",
    "hosiery_fix", "outfit_plan", "hair_flow_plan", "costume_fit_fix",
    "support_rig_cleanup", "transparent_material_fix", "material_texture_enhance_plan",
    "prop_plan", "add_race_feature", "battle_damage", "add_skin_mark",
    "shadow_plan", "reflection_plan", "foreground_plan", "clone_plan",
    "levitate_plan", "subject_harmonize_plan", "image_blend_plan", "vfx_plan",
    "lens_fx_plan", "lighting_reshape", "virtual_lighting_plan",
    "background_tone", "grading_plan", "color_match", "blur_plan", "sky_plan",
    "depth_atmosphere_plan", "outpaint_plan", "poster_plan", "frame_plan",
    "text_plan", "stylize_plan",
}

MODULE_REQUIRED = {"goal", "authorized_area", "preserve", "change", "integrate", "acceptance"}
EFFECT_REQUIRED = {
    "effect_id", "type", "variant", "source_and_cause", "vfx_zone",
    "authorized_area", "anchor", "depth_order", "visual_description",
    "material_emission", "dynamics", "environment_interaction", "camera_response",
    "intensity", "relight_and_blend", "anti_sticker", "acceptance",
}
DEPTH_VALUES = {"behind_subject", "around_subject", "in_front_of_subject"}

LIGHT_REQUIRED = {
    "light_id", "role", "motivation", "source_position", "direction_and_elevation",
    "color", "hardness", "spread", "intensity", "distance_falloff",
    "affected_surfaces", "shadow_behavior", "exclude",
}

BLEND_REQUIRED = {
    "base_image", "donor_images", "alignment", "blend_method",
    "opacity_or_strength", "transition_zone", "color_harmonization",
    "depth_and_occlusion", "seam_healing",
}


def resolve_target(root: Any, path: str) -> list[Any]:
    values = [root]
    for raw_part in path.split("."):
        is_array = raw_part.endswith("[]")
        part = raw_part[:-2] if is_array else raw_part
        next_values: list[Any] = []
        for value in values:
            if not isinstance(value, dict) or part not in value:
                continue
            child = value[part]
            if is_array:
                if isinstance(child, list):
                    next_values.extend(child)
            else:
                next_values.append(child)
        values = next_values
        if not values:
            break
    return values


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        outer = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"外层 JSON 无法读取或解析：{exc}"], warnings

    if not isinstance(outer, dict):
        return ["外层必须是 JSON object"], warnings

    missing_outer = sorted(OUTER_REQUIRED - outer.keys())
    if missing_outer:
        errors.append(f"缺少外层键：{', '.join(missing_outer)}")

    preset_id = outer.get("id")
    if not isinstance(preset_id, str) or not re.fullmatch(r"f_[a-z0-9]+_[a-z0-9]+(?:-[a-z0-9]+)*", preset_id):
        errors.append("id 必须匹配 f_<category>_<kebab-slug>")
    if outer.get("category") not in CATEGORIES:
        errors.append("category 不在允许枚举中")
    if outer.get("_isFactory") is not True:
        errors.append("_isFactory 必须为 true")
    if not isinstance(outer.get("refImages"), list):
        errors.append("refImages 必须是 array")
    if not isinstance(outer.get("params"), list):
        errors.append("params 必须是 array")

    content_raw = outer.get("content")
    if not isinstance(content_raw, str):
        return errors + ["content 必须是 JSON 字符串，不是嵌套 object"], warnings
    if "\n" in content_raw or "\r" in content_raw:
        errors.append("content 必须是单行字符串")
    try:
        content = json.loads(content_raw)
    except json.JSONDecodeError as exc:
        return errors + [f"content 反序列化失败：{exc}"], warnings
    if not isinstance(content, dict):
        return errors + ["content 反序列化后必须是 object"], warnings

    missing_inner = sorted(INNER_REQUIRED - content.keys())
    if missing_inner:
        errors.append(f"缺少内层键：{', '.join(missing_inner)}")

    strategy = content.get("execution_strategy")
    if strategy not in {"single_pass", "ordered_micro_passes"}:
        errors.append("execution_strategy 必须是 single_pass 或 ordered_micro_passes")
    if strategy == "ordered_micro_passes" and not isinstance(content.get("pass_plan"), list):
        errors.append("ordered_micro_passes 必须提供 pass_plan array")

    profile = content.get("executor_profile")
    if isinstance(profile, dict):
        reliability = profile.get("lock_reliability")
        if reliability not in {"strong", "best_effort"}:
            errors.append("executor_profile.lock_reliability 必须是 strong 或 best_effort")
    else:
        errors.append("executor_profile 必须是 object")

    present_modules = sorted(MODULES & content.keys())
    if not present_modules:
        errors.append("content 至少要启用一个规范模块")
    for key in present_modules:
        module = content[key]
        if not isinstance(module, dict):
            errors.append(f"{key} 必须是 object")
            continue
        missing_fields = sorted(MODULE_REQUIRED - module.keys())
        if missing_fields:
            errors.append(f"{key} 缺少五段式字段：{', '.join(missing_fields)}")
        if not module.get("integrate"):
            errors.append(f"{key}.integrate 不得为空")
        acceptance = module.get("acceptance")
        if not isinstance(acceptance, list) or len(acceptance) < 2:
            errors.append(f"{key}.acceptance 至少需要 2 条可观察验收")

    vfx = content.get("vfx_plan")
    if isinstance(vfx, dict):
        effects = vfx.get("effects")
        if not isinstance(effects, list) or not effects:
            errors.append("vfx_plan.effects 必须是非空 array")
        else:
            for index, effect in enumerate(effects):
                label = f"vfx_plan.effects[{index}]"
                if not isinstance(effect, dict):
                    errors.append(f"{label} 必须是 object")
                    continue
                missing = sorted(EFFECT_REQUIRED - effect.keys())
                if missing:
                    errors.append(f"{label} 缺少：{', '.join(missing)}")
                if effect.get("depth_order") not in DEPTH_VALUES:
                    errors.append(f"{label}.depth_order 非法")
                anti_sticker = effect.get("anti_sticker")
                if not isinstance(anti_sticker, list) or len(anti_sticker) < 3:
                    errors.append(f"{label}.anti_sticker 至少需要 3 条")
                effect_acceptance = effect.get("acceptance")
                if not isinstance(effect_acceptance, list) or len(effect_acceptance) < 2:
                    errors.append(f"{label}.acceptance 至少需要 2 条")
                emission = effect.get("material_emission")
                if isinstance(emission, dict) and emission.get("emissive", True) and emission.get("strength", 0) > 0:
                    if "vfx_relight_mask" not in effect:
                        errors.append(f"{label} 为自发光效果但缺少 vfx_relight_mask")

    virtual_lighting = content.get("virtual_lighting_plan")
    if isinstance(virtual_lighting, dict):
        change = virtual_lighting.get("change")
        lights = change.get("lights") if isinstance(change, dict) else None
        if not isinstance(lights, list) or not lights:
            errors.append("virtual_lighting_plan.change.lights 必须是非空 array")
        else:
            for index, light in enumerate(lights):
                if not isinstance(light, dict):
                    errors.append(f"virtual_lighting_plan.change.lights[{index}] 必须是 object")
                    continue
                missing = sorted(LIGHT_REQUIRED - light.keys())
                if missing:
                    errors.append(
                        f"virtual_lighting_plan.change.lights[{index}] 缺少：{', '.join(missing)}"
                    )

    image_blend = content.get("image_blend_plan")
    if isinstance(image_blend, dict):
        change = image_blend.get("change")
        if not isinstance(change, dict):
            errors.append("image_blend_plan.change 必须是 object")
        else:
            missing = sorted(BLEND_REQUIRED - change.keys())
            if missing:
                errors.append(f"image_blend_plan.change 缺少：{', '.join(missing)}")
            donors = change.get("donor_images")
            if not isinstance(donors, list) or not donors:
                errors.append("image_blend_plan.change.donor_images 必须是非空 array")
            else:
                for index, donor in enumerate(donors):
                    if not isinstance(donor, dict) or not {"ref", "transfer_only", "do_not_transfer"} <= donor.keys():
                        errors.append(
                            f"image_blend_plan.change.donor_images[{index}] 缺少 ref/transfer_only/do_not_transfer"
                        )
        if not isinstance(content.get("reference_roles"), list):
            errors.append("启用 image_blend_plan 时必须提供 reference_roles")
        if not outer.get("refImages"):
            errors.append("启用 image_blend_plan 时外层 refImages 不得为空")

    params = outer.get("params")
    if isinstance(params, list):
        required_param = {"key", "label", "type", "min", "max", "default", "step", "target"}
        for index, param in enumerate(params):
            label = f"params[{index}]"
            if not isinstance(param, dict):
                errors.append(f"{label} 必须是 object")
                continue
            missing = sorted(required_param - param.keys())
            if missing:
                errors.append(f"{label} 缺少：{', '.join(missing)}")
                continue
            if param.get("type") != "number":
                errors.append(f"{label}.type 必须为 number")
            values = resolve_target(content, str(param.get("target")))
            if not values:
                errors.append(f"{label}.target 不存在：{param.get('target')}")
            elif any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in values):
                errors.append(f"{label}.target 未全部指向数值")
            elif param.get("default") not in values:
                warnings.append(f"{label}.default 与 target 当前值不一致")

    negative = content.get("negative_prompt")
    if isinstance(negative, str):
        count = len([item for item in re.split(r"[,，;；]", negative) if item.strip()])
        if count > 20:
            warnings.append("negative_prompt 超过 20 项，建议改用更具体的正向终态描述")

    return errors, warnings


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print("用法：python validate_preset.py <preset.json>", file=sys.stderr)
        return 2
    errors, warnings = validate(Path(sys.argv[1]))
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"验证失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"验证通过：0 个错误，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
