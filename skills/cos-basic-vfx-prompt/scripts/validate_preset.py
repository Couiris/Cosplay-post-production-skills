#!/usr/bin/env python3
"""Validate a cos-basic-vfx-prompt preset using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


OUTER_REQUIRED = {
    "id", "title", "content", "params", "category", "subCategory",
    "refImages", "_isFactory",
}

INNER_REQUIRED = {
    "role_instruction", "task_summary", "photo_readout", "executor_profile",
    "execution_strategy", "priority_order", "subject_lock_contract",
    "geometry_camera_lock_contract", "background_lock_contract",
    "subject_light_profile", "authorization_contract", "integration",
    "acceptance_tests", "retry_policy", "constraints", "negative_prompt",
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
    "text_plan", "stylize_plan", "edge_halo_spill_fix", "capture_match_plan",
    "output_finish_plan",
}

MODULE_REQUIRED = {"goal", "authorized_area", "preserve", "change", "integrate", "acceptance"}
EFFECT_REQUIRED = {
    "effect_id", "type", "variant", "composition_role", "source_and_cause",
    "vfx_zone", "authorized_area", "anchor", "depth_order", "silhouette_clearance",
    "density_budget", "visual_description", "material_emission", "dynamics",
    "environment_interaction", "camera_response", "intensity", "relight_and_blend",
    "anti_sticker", "acceptance",
}
DEPTH_VALUES = {"behind_subject", "around_subject", "in_front_of_subject"}
COMPOSITION_ROLES = {"primary", "secondary", "atmosphere"}
DENSITY_REQUIRED = {"coverage_percent", "focal_exclusion", "distribution"}
RELIGHT_REQUIRED = {
    "reachable_surfaces", "tint", "max_luminance_delta", "falloff", "occlusion_stop",
}

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
DONOR_DETAIL_REQUIRED = {
    "source_region", "target_region", "anchor_map", "transform_or_warp", "method",
    "strength", "transition_zone", "depth_and_occlusion", "contact_and_shadow",
}
MATERIAL_REQUIRED = {
    "material_type", "zone", "source_evidence", "source_confidence", "micro_texture",
    "roughness", "highlight_shape", "color_depth", "detail_scale", "strength",
    "do_not_invent",
}
LIGHT_ROLES = {"key", "fill", "rim", "practical", "gobo", "bounce", "underlight"}
LIGHT_HARDNESS = {"hard", "semi_soft", "soft"}

PROFILE_REQUIRED = {
    "target_family", "mask_support", "multi_reference_support", "text_rendering",
    "output_size", "lock_reliability",
}
AUTH_REQUIRED = {
    "per_module", "authorized_change_mask", "unchanged_region_mask",
    "mask_enforcement", "lock_reliability", "face_clean_zone",
}
PASS_REQUIRED = {
    "pass_id", "input_basis", "modules", "authorized_area", "preserve", "acceptance",
}
CORE_OBJECTS = {
    "photo_readout", "subject_lock_contract", "geometry_camera_lock_contract",
    "background_lock_contract", "subject_light_profile", "integration",
}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list, tuple, set)):
        return bool(value)
    return value is not None


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
    id_match = re.fullmatch(r"f_([a-z0-9]+)_[a-z0-9]+(?:-[a-z0-9]+)*", preset_id or "")
    if not isinstance(preset_id, str) or not id_match:
        errors.append("id 必须匹配 f_<category>_<kebab-slug>")
    category = outer.get("category")
    if category not in CATEGORIES:
        errors.append("category 不在允许枚举中")
    elif id_match and id_match.group(1) != category:
        errors.append("id 中的 category 必须与外层 category 一致")
    for key in ("title", "subCategory"):
        if not is_nonempty_string(outer.get(key)):
            errors.append(f"{key} 必须是非空字符串")
    if outer.get("_isFactory") is not True:
        errors.append("_isFactory 必须为 true")
    ref_images = outer.get("refImages")
    if not isinstance(ref_images, list):
        errors.append("refImages 必须是 array")
        ref_images = []
    params = outer.get("params")
    if not isinstance(params, list):
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
    for key in ("role_instruction", "task_summary", "priority_order", "negative_prompt"):
        if not is_nonempty_string(content.get(key)):
            errors.append(f"{key} 必须是非空字符串")
    for key in CORE_OBJECTS:
        if not isinstance(content.get(key), dict) or not content.get(key):
            errors.append(f"{key} 必须是非空 object")

    strategy = content.get("execution_strategy")
    strategies = {"single_pass", "ordered_micro_passes", "checkpointed_multi_turn"}
    if strategy not in strategies:
        errors.append("execution_strategy 必须是 single_pass、ordered_micro_passes 或 checkpointed_multi_turn")

    profile = content.get("executor_profile")
    if isinstance(profile, dict):
        missing = sorted(PROFILE_REQUIRED - profile.keys())
        if missing:
            errors.append(f"executor_profile 缺少：{', '.join(missing)}")
        if not is_nonempty_string(profile.get("target_family")):
            errors.append("executor_profile.target_family 必须是非空字符串")
        if profile.get("mask_support") not in {"explicit", "semantic", "host_composite", "none", "unknown"}:
            errors.append("executor_profile.mask_support 非法")
        if profile.get("multi_reference_support") not in {"supported", "unsupported", "unknown"}:
            errors.append("executor_profile.multi_reference_support 非法")
        if not is_nonempty_string(profile.get("text_rendering")):
            errors.append("executor_profile.text_rendering 必须是非空字符串")
        if not is_nonempty_string(profile.get("output_size")):
            errors.append("executor_profile.output_size 必须是非空字符串")
        if profile.get("lock_reliability") not in {"strong", "best_effort"}:
            errors.append("executor_profile.lock_reliability 必须是 strong 或 best_effort")
        if "multi_turn_support" in profile and profile["multi_turn_support"] not in {True, False, "unknown"}:
            errors.append("executor_profile.multi_turn_support 必须是 true、false 或 unknown")
        if strategy == "checkpointed_multi_turn" and profile.get("multi_turn_support") is not True:
            errors.append("checkpointed_multi_turn 要求 executor_profile.multi_turn_support=true")
    else:
        errors.append("executor_profile 必须是 object")
        profile = {}

    present_modules = sorted(MODULES & content.keys())
    if not present_modules:
        errors.append("content 至少要启用一个规范模块")
    unknown_modules = sorted(
        key for key in content
        if (key.endswith("_plan") or key.endswith("_fix"))
        and key not in MODULES and key not in {"pass_plan"}
    )
    if unknown_modules:
        errors.append(f"发现未注册或疑似拼错的模块：{', '.join(unknown_modules)}")
    for key in present_modules:
        module = content[key]
        if not isinstance(module, dict):
            errors.append(f"{key} 必须是 object")
            continue
        missing_fields = sorted(MODULE_REQUIRED - module.keys())
        if missing_fields:
            errors.append(f"{key} 缺少五段式字段：{', '.join(missing_fields)}")
        if not is_nonempty_string(module.get("goal")):
            errors.append(f"{key}.goal 必须是非空字符串")
        if not is_nonempty_string(module.get("authorized_area")):
            errors.append(f"{key}.authorized_area 必须是非空字符串")
        preserve = module.get("preserve")
        if not isinstance(preserve, list) or len(preserve) < 2 or not all(is_nonempty_string(x) for x in preserve):
            errors.append(f"{key}.preserve 至少需要 2 条非空保留项")
        for field in ("change", "integrate"):
            if not isinstance(module.get(field), dict) or not module.get(field):
                errors.append(f"{key}.{field} 必须是非空 object")
        acceptance = module.get("acceptance")
        if not isinstance(acceptance, list) or len(acceptance) < 2 or not all(is_nonempty_string(x) for x in acceptance):
            errors.append(f"{key}.acceptance 至少需要 2 条可观察验收")

    low_light = content.get("low_light_rescue")
    if isinstance(low_light, dict):
        low_light_change = low_light.get("change")
        if not isinstance(low_light_change, dict) or low_light_change.get("recoverability") not in {
            "reliable", "limited", "none",
        }:
            errors.append("low_light_rescue.change.recoverability 必须是 reliable、limited 或 none")

    material_plan = content.get("material_texture_enhance_plan")
    if isinstance(material_plan, dict):
        material_change = material_plan.get("change")
        materials = material_change.get("materials") if isinstance(material_change, dict) else None
        if not isinstance(materials, list) or not materials:
            errors.append("material_texture_enhance_plan.change.materials 必须是非空 array")
        else:
            for index, material in enumerate(materials):
                label = f"material_texture_enhance_plan.change.materials[{index}]"
                if not isinstance(material, dict):
                    errors.append(f"{label} 必须是 object")
                    continue
                missing = sorted(MATERIAL_REQUIRED - material.keys())
                if missing:
                    errors.append(f"{label} 缺少：{', '.join(missing)}")
                if material.get("source_confidence") not in {"high", "medium", "low"}:
                    errors.append(f"{label}.source_confidence 非法")
                strength = material.get("strength")
                if not is_number(strength) or not 0 <= strength <= 100:
                    errors.append(f"{label}.strength 必须在 0–100")
                for field in MATERIAL_REQUIRED - {"strength", "do_not_invent"}:
                    if not is_nonempty_string(material.get(field)):
                        errors.append(f"{label}.{field} 必须是非空字符串")
                if not isinstance(material.get("do_not_invent"), list) or not material.get("do_not_invent"):
                    errors.append(f"{label}.do_not_invent 必须是非空 array")

    if low_light is not None and material_plan is not None and strategy == "single_pass":
        errors.append("low_light_rescue 与 material_texture_enhance_plan 同时启用时必须分阶段执行")

    vfx = content.get("vfx_plan")
    if isinstance(vfx, dict):
        effects = vfx.get("effects")
        if not isinstance(effects, list) or not effects:
            errors.append("vfx_plan.effects 必须是非空 array")
        else:
            effect_ids: set[str] = set()
            for index, effect in enumerate(effects):
                label = f"vfx_plan.effects[{index}]"
                if not isinstance(effect, dict):
                    errors.append(f"{label} 必须是 object")
                    continue
                missing = sorted(EFFECT_REQUIRED - effect.keys())
                if missing:
                    errors.append(f"{label} 缺少：{', '.join(missing)}")
                effect_id = effect.get("effect_id")
                if not is_nonempty_string(effect_id):
                    errors.append(f"{label}.effect_id 必须是非空字符串")
                elif effect_id in effect_ids:
                    errors.append(f"{label}.effect_id 重复：{effect_id}")
                else:
                    effect_ids.add(effect_id)
                for field in (
                    "type", "variant", "source_and_cause", "vfx_zone", "authorized_area",
                    "anchor", "visual_description",
                ):
                    if not is_nonempty_string(effect.get(field)):
                        errors.append(f"{label}.{field} 必须是非空字符串")
                if effect.get("depth_order") not in DEPTH_VALUES:
                    errors.append(f"{label}.depth_order 非法")
                if effect.get("composition_role") not in COMPOSITION_ROLES:
                    errors.append(f"{label}.composition_role 非法")
                if not is_nonempty_string(effect.get("silhouette_clearance")):
                    errors.append(f"{label}.silhouette_clearance 必须是非空字符串")
                density = effect.get("density_budget")
                if not isinstance(density, dict):
                    errors.append(f"{label}.density_budget 必须是 object")
                else:
                    missing_density = sorted(DENSITY_REQUIRED - density.keys())
                    if missing_density:
                        errors.append(f"{label}.density_budget 缺少：{', '.join(missing_density)}")
                    coverage = density.get("coverage_percent")
                    if not is_number(coverage) or not 0 <= coverage <= 100:
                        errors.append(f"{label}.density_budget.coverage_percent 必须在 0–100")
                    for field in ("focal_exclusion", "distribution"):
                        if not is_nonempty_string(density.get(field)):
                            errors.append(f"{label}.density_budget.{field} 必须是非空字符串")
                intensity = effect.get("intensity")
                if not is_number(intensity) or not 0 <= intensity <= 100:
                    errors.append(f"{label}.intensity 必须在 0–100")
                anti_sticker = effect.get("anti_sticker")
                if not isinstance(anti_sticker, list) or len(anti_sticker) < 3:
                    errors.append(f"{label}.anti_sticker 至少需要 3 条")
                effect_acceptance = effect.get("acceptance")
                if not isinstance(effect_acceptance, list) or len(effect_acceptance) < 2:
                    errors.append(f"{label}.acceptance 至少需要 2 条")
                emission = effect.get("material_emission")
                for field in (
                    "material_emission", "dynamics", "environment_interaction",
                    "camera_response", "relight_and_blend",
                ):
                    if not isinstance(effect.get(field), dict) or not effect.get(field):
                        errors.append(f"{label}.{field} 必须是非空 object")
                if isinstance(emission, dict) and emission.get("emissive", True) and emission.get("strength", 0) > 0:
                    relight = effect.get("vfx_relight_mask")
                    if not isinstance(relight, dict):
                        errors.append(f"{label} 为自发光效果但缺少 vfx_relight_mask")
                    else:
                        missing_relight = sorted(RELIGHT_REQUIRED - relight.keys())
                        if missing_relight:
                            errors.append(f"{label}.vfx_relight_mask 缺少：{', '.join(missing_relight)}")
                        if not isinstance(relight.get("reachable_surfaces"), list) or not relight.get("reachable_surfaces"):
                            errors.append(f"{label}.vfx_relight_mask.reachable_surfaces 必须是非空 array")
                        delta = relight.get("max_luminance_delta")
                        if not is_number(delta) or not 0 <= delta <= 100:
                            errors.append(f"{label}.vfx_relight_mask.max_luminance_delta 必须在 0–100")
                        for field in ("tint", "falloff", "occlusion_stop"):
                            if not is_nonempty_string(relight.get(field)):
                                errors.append(f"{label}.vfx_relight_mask.{field} 必须是非空字符串")
            if len(effects) > 1:
                for field in ("global_moment", "palette_relationship", "shared_environment_response"):
                    if not is_nonempty(vfx.get(field)):
                        errors.append(f"多特效 vfx_plan 必须提供 {field}")
                for index, effect in enumerate(effects):
                    weight = effect.get("hierarchy_weight") if isinstance(effect, dict) else None
                    if not is_number(weight) or not 0 <= weight <= 100:
                        errors.append(f"vfx_plan.effects[{index}].hierarchy_weight 必须在 0–100")
                primary_count = sum(
                    1 for effect in effects
                    if isinstance(effect, dict) and effect.get("composition_role") == "primary"
                )
                if primary_count not in {1, 2}:
                    errors.append("多特效 vfx_plan 必须有 1 个 primary，或在双主效果时有 2 个 primary")
                if primary_count == 2 and not is_nonempty_string(vfx.get("co_dominant_reason")):
                    errors.append("双主效果必须提供 vfx_plan.co_dominant_reason")

    virtual_lighting = content.get("virtual_lighting_plan")
    if isinstance(virtual_lighting, dict):
        change = virtual_lighting.get("change")
        lights = change.get("lights") if isinstance(change, dict) else None
        if isinstance(change, dict):
            if not is_nonempty_string(change.get("lighting_goal")):
                errors.append("virtual_lighting_plan.change.lighting_goal 必须是非空字符串")
            if change.get("preserve_base_exposure") is not True:
                errors.append("virtual_lighting_plan.change.preserve_base_exposure 必须为 true")
        if not isinstance(lights, list) or not lights:
            errors.append("virtual_lighting_plan.change.lights 必须是非空 array")
        else:
            light_ids: set[str] = set()
            for index, light in enumerate(lights):
                label = f"virtual_lighting_plan.change.lights[{index}]"
                if not isinstance(light, dict):
                    errors.append(f"{label} 必须是 object")
                    continue
                missing = sorted(LIGHT_REQUIRED - light.keys())
                if missing:
                    errors.append(f"{label} 缺少：{', '.join(missing)}")
                light_id = light.get("light_id")
                if not is_nonempty_string(light_id):
                    errors.append(f"{label}.light_id 必须是非空字符串")
                elif light_id in light_ids:
                    errors.append(f"{label}.light_id 重复：{light_id}")
                else:
                    light_ids.add(light_id)
                if light.get("role") not in LIGHT_ROLES:
                    errors.append(f"{label}.role 非法")
                if light.get("hardness") not in LIGHT_HARDNESS:
                    errors.append(f"{label}.hardness 非法")
                for field in (
                    "motivation", "source_position", "direction_and_elevation", "color",
                    "spread", "distance_falloff", "shadow_behavior",
                ):
                    if not is_nonempty_string(light.get(field)):
                        errors.append(f"{label}.{field} 必须是非空字符串")
                intensity = light.get("intensity")
                if not is_number(intensity) or not 0 <= intensity <= 100:
                    errors.append(f"{label}.intensity 必须在 0–100")
                if not isinstance(light.get("affected_surfaces"), list) or not light.get("affected_surfaces"):
                    errors.append(f"{label}.affected_surfaces 必须是非空 array")
                if not isinstance(light.get("exclude"), list) or not light.get("exclude"):
                    errors.append(f"{label}.exclude 必须是非空 array")

    image_blend = content.get("image_blend_plan")
    if isinstance(image_blend, dict):
        if profile.get("multi_reference_support") != "supported":
            errors.append("启用 image_blend_plan 必须确认 executor_profile.multi_reference_support=supported")
        change = image_blend.get("change")
        if not isinstance(change, dict):
            errors.append("image_blend_plan.change 必须是 object")
        else:
            missing = sorted(BLEND_REQUIRED - change.keys())
            if missing:
                errors.append(f"image_blend_plan.change 缺少：{', '.join(missing)}")
            if change.get("blend_method") not in {
                "masked_normal", "screen_lighten", "multiply_dark",
                "soft_light_texture", "depth_aware_composite",
            }:
                errors.append("image_blend_plan.change.blend_method 非法")
            blend_strength = change.get("opacity_or_strength")
            if not is_number(blend_strength) or not 0 <= blend_strength <= 100:
                errors.append("image_blend_plan.change.opacity_or_strength 必须在 0–100")
            donors = change.get("donor_images")
            if not isinstance(donors, list) or not donors:
                errors.append("image_blend_plan.change.donor_images 必须是非空 array")
            else:
                donor_refs: set[str] = set()
                for index, donor in enumerate(donors):
                    label = f"image_blend_plan.change.donor_images[{index}]"
                    if not isinstance(donor, dict) or not {"ref", "transfer_only", "do_not_transfer"} <= donor.keys():
                        errors.append(f"{label} 缺少 ref/transfer_only/do_not_transfer")
                        continue
                    if donor.get("ref") not in ref_images:
                        errors.append(f"{label}.ref 未出现在外层 refImages")
                    if donor.get("ref") in donor_refs:
                        errors.append(f"{label}.ref 重复：{donor.get('ref')}")
                    elif is_nonempty_string(donor.get("ref")):
                        donor_refs.add(donor["ref"])
                    if not isinstance(donor.get("transfer_only"), list) or not donor.get("transfer_only"):
                        errors.append(f"{label}.transfer_only 必须是非空 array")
                    if not isinstance(donor.get("do_not_transfer"), list):
                        errors.append(f"{label}.do_not_transfer 必须是 array")
                    if len(donors) > 1:
                        missing_detail = sorted(DONOR_DETAIL_REQUIRED - donor.keys())
                        if missing_detail:
                            errors.append(f"多供体 {label} 缺少独立合成字段：{', '.join(missing_detail)}")
                        strength = donor.get("strength")
                        if "strength" in donor and (not is_number(strength) or not 0 <= strength <= 100):
                            errors.append(f"{label}.strength 必须在 0–100")
                        if donor.get("method") not in {
                            "masked_normal", "screen_lighten", "multiply_dark",
                            "soft_light_texture", "depth_aware_composite",
                        }:
                            errors.append(f"{label}.method 非法")
                        for field in DONOR_DETAIL_REQUIRED - {"strength"}:
                            if not is_nonempty(donor.get(field)):
                                errors.append(f"{label}.{field} 不得为空")
        if not isinstance(content.get("reference_roles"), list) or not content.get("reference_roles"):
            errors.append("启用 image_blend_plan 时必须提供非空 reference_roles")
        if not ref_images:
            errors.append("启用 image_blend_plan 时外层 refImages 不得为空")

    reference_roles = content.get("reference_roles")
    if ref_images and (not isinstance(reference_roles, list) or not reference_roles):
        errors.append("外层 refImages 非空时必须提供非空 reference_roles")
    if isinstance(reference_roles, list):
        role_indexes: set[int] = set()
        for index, role in enumerate(reference_roles):
            label = f"reference_roles[{index}]"
            if not isinstance(role, dict) or not {"index", "role", "use", "do_not_transfer"} <= role.keys():
                errors.append(f"{label} 缺少 index/role/use/do_not_transfer")
                continue
            role_index = role.get("index")
            if not isinstance(role_index, int) or isinstance(role_index, bool) or role_index < 1:
                errors.append(f"{label}.index 必须是正整数")
            elif role_index in role_indexes:
                errors.append(f"{label}.index 重复：{role_index}")
            else:
                role_indexes.add(role_index)
            for field in ("role", "use"):
                if not is_nonempty_string(role.get(field)):
                    errors.append(f"{label}.{field} 必须是非空字符串")
            if not isinstance(role.get("do_not_transfer"), list):
                errors.append(f"{label}.do_not_transfer 必须是 array")

    auth = content.get("authorization_contract")
    if not isinstance(auth, dict):
        errors.append("authorization_contract 必须是 object")
    else:
        missing = sorted(AUTH_REQUIRED - auth.keys())
        if missing:
            errors.append(f"authorization_contract 缺少：{', '.join(missing)}")
        per_module = auth.get("per_module")
        if not isinstance(per_module, dict):
            errors.append("authorization_contract.per_module 必须是 object")
        else:
            missing_mappings = sorted(set(present_modules) - per_module.keys())
            extra_mappings = sorted(per_module.keys() - set(present_modules))
            if missing_mappings:
                errors.append(f"authorization_contract.per_module 缺少模块：{', '.join(missing_mappings)}")
            if extra_mappings:
                errors.append(f"authorization_contract.per_module 含未启用模块：{', '.join(extra_mappings)}")
            for module_name, region in per_module.items():
                if not is_nonempty(region):
                    errors.append(f"authorization_contract.per_module.{module_name} 不得为空")
        for field in ("authorized_change_mask", "unchanged_region_mask", "face_clean_zone"):
            if not is_nonempty(auth.get(field)):
                errors.append(f"authorization_contract.{field} 不得为空")
        enforcement = auth.get("mask_enforcement")
        if enforcement not in {"explicit_mask", "semantic_mask", "host_composite"}:
            errors.append("authorization_contract.mask_enforcement 非法")
        if auth.get("lock_reliability") not in {"strong", "best_effort"}:
            errors.append("authorization_contract.lock_reliability 必须是 strong 或 best_effort")
        elif auth.get("lock_reliability") != profile.get("lock_reliability"):
            errors.append("authorization_contract 与 executor_profile 的 lock_reliability 必须一致")
        if auth.get("lock_reliability") == "strong" and enforcement == "semantic_mask":
            errors.append("semantic_mask 不得声明 strong 锁定可靠性")
        if profile.get("lock_reliability") == "strong" and profile.get("mask_support") in {"semantic", "none", "unknown"}:
            errors.append("执行器缺少显式蒙版/宿主合成能力时不得声明 strong 锁定")

    pass_plan = content.get("pass_plan")
    if strategy in {"ordered_micro_passes", "checkpointed_multi_turn"}:
        if not isinstance(pass_plan, list) or not pass_plan:
            errors.append(f"{strategy} 必须提供非空 pass_plan array")
        else:
            assigned: list[str] = []
            for index, step in enumerate(pass_plan):
                label = f"pass_plan[{index}]"
                if not isinstance(step, dict):
                    errors.append(f"{label} 必须是 object")
                    continue
                missing = sorted(PASS_REQUIRED - step.keys())
                if missing:
                    errors.append(f"{label} 缺少：{', '.join(missing)}")
                expected_basis = "original_input" if index == 0 else "previous_pass_output"
                if step.get("input_basis") != expected_basis:
                    errors.append(f"{label}.input_basis 必须为 {expected_basis}")
                step_modules = step.get("modules")
                if not isinstance(step_modules, list) or not step_modules:
                    errors.append(f"{label}.modules 必须是非空 array")
                else:
                    assigned.extend(step_modules)
                    unknown = sorted(set(step_modules) - set(present_modules))
                    if unknown:
                        errors.append(f"{label}.modules 含未启用模块：{', '.join(unknown)}")
                if not is_nonempty_string(step.get("authorized_area")):
                    errors.append(f"{label}.authorized_area 必须是非空字符串")
                for field in ("preserve", "acceptance"):
                    if not isinstance(step.get(field), list) or not step.get(field):
                        errors.append(f"{label}.{field} 必须是非空 array")
                if strategy == "checkpointed_multi_turn":
                    if step.get("checkpoint_required") is not True:
                        errors.append(f"{label}.checkpoint_required 必须为 true")
                    if not is_nonempty(step.get("continue_only_if")):
                        errors.append(f"{label}.continue_only_if 不得为空")
                    if step.get("rollback_to") != "previous_accepted_output":
                        errors.append(f"{label}.rollback_to 必须为 previous_accepted_output")
            duplicate_assignments = sorted({name for name in assigned if assigned.count(name) > 1})
            if duplicate_assignments:
                errors.append(f"pass_plan 模块重复分配：{', '.join(duplicate_assignments)}")
            missing_assignments = sorted(set(present_modules) - set(assigned))
            if missing_assignments:
                errors.append(f"pass_plan 未覆盖启用模块：{', '.join(missing_assignments)}")

    acceptance_tests = content.get("acceptance_tests")
    if (
        not isinstance(acceptance_tests, list)
        or len(acceptance_tests) < 3
        or not all(is_nonempty_string(item) for item in acceptance_tests)
    ):
        errors.append("acceptance_tests 至少需要 3 条")
    retry = content.get("retry_policy")
    if not isinstance(retry, dict):
        errors.append("retry_policy 必须是 object")
    else:
        max_variants = retry.get("max_variants")
        if not isinstance(max_variants, int) or isinstance(max_variants, bool) or not 1 <= max_variants <= 5:
            errors.append("retry_policy.max_variants 必须是 1–5 的整数")
        if not is_nonempty_string(retry.get("rule")):
            errors.append("retry_policy.rule 必须是非空字符串")
    constraints = content.get("constraints")
    if not isinstance(constraints, dict) or not constraints:
        errors.append("constraints 必须是非空 object")
    elif not isinstance(constraints.get("must_not"), list) or not constraints.get("must_not"):
        errors.append("constraints.must_not 必须是非空 array")

    if isinstance(params, list):
        required_param = {"key", "label", "type", "min", "max", "default", "step", "target"}
        seen_keys: set[str] = set()
        for index, param in enumerate(params):
            label = f"params[{index}]"
            if not isinstance(param, dict):
                errors.append(f"{label} 必须是 object")
                continue
            missing = sorted(required_param - param.keys())
            if missing:
                errors.append(f"{label} 缺少：{', '.join(missing)}")
                continue
            key = param.get("key")
            if not is_nonempty_string(key):
                errors.append(f"{label}.key 必须是非空字符串")
            elif key in seen_keys:
                errors.append(f"{label}.key 重复：{key}")
            else:
                seen_keys.add(key)
            if param.get("type") != "number":
                errors.append(f"{label}.type 必须为 number")
            minimum, maximum = param.get("min"), param.get("max")
            default, step = param.get("default"), param.get("step")
            if not all(is_number(value) for value in (minimum, maximum, default, step)):
                errors.append(f"{label} 的 min/max/default/step 必须全为数值")
            elif minimum > maximum or not minimum <= default <= maximum or step <= 0:
                errors.append(f"{label} 的数值范围或 step 非法")
            target = param.get("target")
            if not is_nonempty_string(target):
                errors.append(f"{label}.target 必须是非空字符串")
                continue
            values = resolve_target(content, target)
            if not values:
                errors.append(f"{label}.target 不存在：{target}")
            elif any(not is_number(value) for value in values):
                errors.append(f"{label}.target 未全部指向数值")
            else:
                if is_number(minimum) and is_number(maximum) and any(not minimum <= value <= maximum for value in values):
                    errors.append(f"{label}.target 当前值超出 min/max")
                if any(value != default for value in values):
                    warnings.append(f"{label}.default 与一个或多个 target 当前值不一致")

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
