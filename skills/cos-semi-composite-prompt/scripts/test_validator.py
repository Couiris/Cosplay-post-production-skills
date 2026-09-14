#!/usr/bin/env python3
"""Mutation tests for the two-stage composite pair validator."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

from validate_pair import COMPOSITE_ORDER, LAYER_NAMES, MODE, validate_pair


def layers() -> dict[str, Any]:
    return {
        name: {"enabled": False, "richness": 0, "detail_precision": 0}
        for name in LAYER_NAMES
    }


def base_content(stage: int) -> dict[str, Any]:
    content: dict[str, Any] = {
        "role_instruction": "执行 COS 两阶段合成并遵守所有显式遮罩。",
        "intent_card": {"requested_changes": ["测试场景"], "forbidden_changes": ["重绘人物"]},
        "executor_profile": {
            "target_family": "nano_banana_or_gemini_image_edit",
            "subject_cutout_available": True,
            "mask_support": "explicit",
            "rgba_patch_output": True,
            "absolute_coordinate_composite": True,
            "pixel_diff_validation": True,
            "multi_reference_support": "supported",
            "multi_turn_support": True,
            "lock_reliability": "strong",
        },
        "execution_status": "executable",
        "pair_id": "pair_test_scene",
        "pair_manifest": {
            "schema_version": "2.0",
            "skill_mode": MODE,
            "stage_index": stage,
            "stage1_required_outputs": ["background_plate_rgba", "shadow_layer_rgba"],
            "stage2_required_inputs": ["stage1_output", "locked_shadow_mask"],
            "shared_contract_fields": ["geometry_contract", "subject_light_profile"],
            "runtime_hashes": {"resolver": "host_before_each_stage"},
        },
        "runtime_bindings": [],
        "geometry_contract": {"canvas": "locked"},
        "camera_calibration": {"horizon": "locked"},
        "subject_perspective_lock": {"transform": "locked"},
        "subject_scene_scale_contract": {"subject_height": 1.0},
        "scene_layers": layers(),
        "subject_light_profile": {"primary": "input evidence"},
        "environment_light_plan": {"primary": "matches subject"},
        "light_interaction_regions": {"subject_core": "source layer locked"},
        "light_consistency_validation": {"reject": ["opposite shadow"]},
        "light_match_strength": 90,
        "integration": {"blend_strength": 60},
        "validation": {"quality_gates": ["capability", "inheritance", "geometry", "composite", "delivery"]},
        "constraints": {"must_not": ["full-frame model output"]},
        "subject_count": 1 if stage == 1 else 0,
    }
    if MODE == "semi_composite":
        content.update({
            "photographic_fidelity_contract": {"source_basis": "original_photo"},
            "cleanup_contract": {"remove": ["temporary equipment"]},
            "canvas_expansion_contract": {"mode": "original_canvas"},
            "original_scene_geometry_lock": {"wall_ceiling": "locked"},
            "ground_plane_registration": {"evidence": ["line_1", "line_2", "line_3", "line_4"]},
            "retained_original_scene": {"wall": "visible pixels locked"},
            "camera_match": {"depth_strength": 60},
        })
    else:
        content.update({
            "character_worldview_card": {"main_world": "test world"},
            "composition_budget": {"hero_visuals": 1, "support_families": 3, "emissive_sources": 1},
            "vfx_stage_assignment": {"structural": "stage1", "background_overlay": "stage2", "foreground": "final_assembly"},
        })
    if stage == 1:
        content.update({
            "subject_lock_contract": {
                "subjects": [{
                    "subject_id": "subject_1", "source": "cutout_1", "alpha": "alpha_1",
                    "bbox": [10, 10, 100, 200], "centroid": [55, 105],
                    "contact_points": [[50, 200]], "pixel_hash": "hash_subject_1",
                    "occlusion_order": 1,
                }],
                "union_subject_alpha": "alpha_1",
                "subject_transform_allowed": False,
                "subject_repaint_allowed": False,
                "subject_model_output_allowed": False,
            },
            "stage1_execution_contract": {
                "composite_order": COMPOSITE_ORDER,
                "reject_full_frame_subject": True,
            },
            "shadow_controls": {"contact_shadow": 60, "cast_shadow": 50, "ambient_occlusion": 50},
            "base_frame_manifest": {
                "stage1_output_hash": "runtime_hash_stage1", "canvas_size": [1000, 1500],
                "subject_removal_mask": "subject_mask", "locked_shadow_mask": "shadow_mask",
                "asset_addition_mask": "asset_mask", "material_refinement_mask": "material_mask",
                "background_vfx_mask": "vfx_mask",
            },
            "shadow_lock_package": {
                "shadow_mode": "generated", "locked_shadow_mask": "shadow_mask",
                "shadow_reference_pixels": "shadow_pixels", "export_shadow_layer": "shadow_layer_rgba",
                "caster_ids": ["subject_1"],
            },
        })
        if MODE == "semi_composite":
            content["base_frame_manifest"].update({
                "visible_retained_scene_lock": "visible_wall_ceiling",
                "occluded_reconstruction_mask": "occluded_wall_ground",
                "outpaint_mask": "none",
            })
    else:
        content.update({
            "base_frame_lock": {
                "immutable_base_image": "stage1_output", "global_generative_render": False,
                "transform_allowed": False, "mask_coordinates": "canvas_absolute",
            },
            "stage2_execution_contract": {
                "authorized_change_mask": "subject_removal_mask OR shadow_removal_mask OR asset_addition_mask OR material_refinement_mask OR background_vfx_mask",
                "reject_full_frame_model_output": True,
            },
            "shadow_removal_contract": {
                "shadow_removal_strength": 100, "source_mask": "locked_shadow_mask from stage1",
                "no_restore": True,
            },
            "stage2_overlay_layers": layers(),
            "stage2_asset_expansion": {"asset_expansion_intensity": 65},
            "background_refinement": {"material_refinement": 75},
            "background_vfx": {"background_vfx_intensity": 55, "background_particle_density": 50},
            "final_assembly_manifest": {"layer_order": COMPOSITE_ORDER},
        })
        if MODE == "semi_composite":
            content.update({
                "background_only_contract": {"subject_count": 0},
                "stage2_asset_refinement_manifest": {"asset_ids": ["stage1_asset_1"]},
            })
    return content


def outer(stage: int, content: dict[str, Any]) -> dict[str, Any]:
    suffix = "step1-subject-shadow-composite" if stage == 1 else "step2-subject-removed-refined-plate"
    params = [{
        "key": "light_match_strength", "label": "光源匹配", "type": "number",
        "min": 0, "max": 100, "default": 90, "step": 5,
        "target": "light_match_strength",
    }]
    if stage == 2:
        params.append({
            "key": "shadow_removal_strength", "label": "影子移除", "type": "number",
            "min": 100, "max": 100, "default": 100, "step": 1,
            "target": "shadow_removal_contract.shadow_removal_strength",
        })
    return {
        "id": f"f_scene_test-{suffix}", "title": f"阶段{stage}测试", "content": json.dumps(content, ensure_ascii=False, separators=(",", ":")),
        "params": params, "category": "scene", "subCategory": "测试场景",
        "refImages": [], "_isFactory": True,
    }


def run_pair(step1: dict[str, Any], step2: dict[str, Any]) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="cos-composite-pair-") as temp_dir:
        p1, p2 = Path(temp_dir) / "step1.json", Path(temp_dir) / "step2.json"
        p1.write_text(json.dumps(step1, ensure_ascii=False), encoding="utf-8")
        p2.write_text(json.dumps(step2, ensure_ascii=False), encoding="utf-8")
        errors, _ = validate_pair(p1, p2)
        return errors


def mutate(preset: dict[str, Any], fn: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    result = copy.deepcopy(preset)
    content = json.loads(result["content"])
    fn(content)
    result["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    return result


class PairValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.step1 = outer(1, base_content(1))
        self.step2 = outer(2, base_content(2))

    def reject(self, step1: dict[str, Any], step2: dict[str, Any], fragment: str) -> None:
        errors = run_pair(step1, step2)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_valid_pair(self) -> None:
        self.assertEqual(run_pair(self.step1, self.step2), [])

    def test_shared_light_drift(self) -> None:
        bad = mutate(self.step2, lambda c: c["subject_light_profile"].update(primary="changed"))
        self.reject(self.step1, bad, "共享字段不一致")

    def test_capability_gate(self) -> None:
        bad = mutate(self.step1, lambda c: c["executor_profile"].update(mask_support="semantic"))
        self.reject(bad, self.step2, "mask_support 必须是 explicit")

    def test_shadow_mask_must_be_authorized(self) -> None:
        bad = mutate(self.step2, lambda c: c["stage2_execution_contract"].update(authorized_change_mask="subject_removal_mask"))
        self.reject(self.step1, bad, "缺少 shadow_removal_mask")

    def test_stage2_scene_layers_are_read_only(self) -> None:
        bad = copy.deepcopy(self.step2)
        bad["params"][0]["target"] = "scene_layers.ground.richness"
        bad["params"][0]["default"] = 0
        self.reject(self.step1, bad, "不得修改阶段 2")

    def test_composite_order(self) -> None:
        bad = mutate(self.step1, lambda c: c["stage1_execution_contract"].update(composite_order=list(reversed(COMPOSITE_ORDER))))
        self.reject(bad, self.step2, "composite_order 非法")

    def test_subject_count_matches_subjects(self) -> None:
        bad = mutate(self.step1, lambda c: c.update(subject_count=2))
        self.reject(bad, self.step2, "subjects[] 长度")

    def test_shadow_none_requires_reason(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["shadow_lock_package"] = {"shadow_mode": "none"}

        self.reject(mutate(self.step1, change), self.step2, "no_shadow_reason")

    def test_placeholder_is_rejected(self) -> None:
        bad = mutate(self.step1, lambda c: c["intent_card"].update(requested_changes=["TODO"]))
        self.reject(bad, self.step2, "占位符")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PairValidatorTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
