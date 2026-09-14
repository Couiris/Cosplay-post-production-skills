#!/usr/bin/env python3
"""Mutation regression tests for validate_preset.py."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

from validate_preset import validate


ROOT = Path(__file__).resolve().parents[1]


def load_outer(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "references" / name).read_text(encoding="utf-8-sig"))


def mutate_content(outer: dict[str, Any], change: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    result = copy.deepcopy(outer)
    content = json.loads(result["content"])
    change(content)
    result["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    return result


def errors_for(outer: dict[str, Any]) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="cos-vfx-validator-") as temp_dir:
        path = Path(temp_dir) / "preset.json"
        path.write_text(json.dumps(outer, ensure_ascii=False), encoding="utf-8")
        errors, _ = validate(path)
        return errors


class ValidatorMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = load_outer("preset-template.json")
        cls.blend = load_outer("lighting-blending-template.json")

    def assert_rejected(self, outer: dict[str, Any], fragment: str) -> None:
        errors = errors_for(outer)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected error containing {fragment!r}, got {errors!r}",
        )

    def test_valid_templates(self) -> None:
        self.assertEqual(errors_for(self.base), [])
        self.assertEqual(errors_for(self.blend), [])

    def test_empty_pass_plan_is_rejected(self) -> None:
        outer = mutate_content(self.blend, lambda content: content.__setitem__("pass_plan", []))
        self.assert_rejected(outer, "非空 pass_plan")

    def test_missing_authorization_mapping_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["authorization_contract"]["per_module"].pop("vfx_plan")

        self.assert_rejected(mutate_content(self.base, change), "per_module 缺少模块")

    def test_unknown_module_typo_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["vfxs_plan"] = content.pop("vfx_plan")

        self.assert_rejected(mutate_content(self.base, change), "疑似拼错")

    def test_bad_parameter_range_is_rejected(self) -> None:
        outer = copy.deepcopy(self.base)
        outer["params"][0]["min"] = 90
        outer["params"][0]["max"] = 10
        self.assert_rejected(outer, "数值范围")

    def test_untraceable_donor_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["image_blend_plan"]["change"]["donor_images"][0]["ref"] = "input_404"

        self.assert_rejected(mutate_content(self.blend, change), "未出现在外层 refImages")

    def test_lock_reliability_mismatch_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["authorization_contract"]["lock_reliability"] = "strong"

        self.assert_rejected(mutate_content(self.base, change), "lock_reliability 必须一致")

    def test_multi_effect_without_coordination_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            effects = content["vfx_plan"]["effects"]
            effects[0]["hierarchy_weight"] = 80
            second = copy.deepcopy(effects[0])
            second["effect_id"] = "vfx_2"
            second["composition_role"] = "secondary"
            second["hierarchy_weight"] = 45
            effects.append(second)

        self.assert_rejected(mutate_content(self.base, change), "global_moment")

    def test_unknown_multi_reference_capability_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["executor_profile"]["multi_reference_support"] = "unknown"

        self.assert_rejected(mutate_content(self.blend, change), "multi_reference_support=supported")

    def test_empty_relight_is_rejected(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["vfx_plan"]["effects"][0]["vfx_relight_mask"] = {}

        self.assert_rejected(mutate_content(self.base, change), "vfx_relight_mask 缺少")

    def test_checkpoint_pass_metadata_is_required(self) -> None:
        def change(content: dict[str, Any]) -> None:
            content["execution_strategy"] = "checkpointed_multi_turn"
            content["executor_profile"]["multi_turn_support"] = True

        self.assert_rejected(mutate_content(self.blend, change), "checkpoint_required")

    def test_material_plan_requires_material_records(self) -> None:
        def change(content: dict[str, Any]) -> None:
            module = content.pop("vfx_plan")
            module["goal"] = "提升现有材质"
            module["change"] = {"strength": 55}
            content["material_texture_enhance_plan"] = module
            content["authorization_contract"]["per_module"] = {
                "material_texture_enhance_plan": module["authorized_area"]
            }

        self.assert_rejected(mutate_content(self.base, change), "change.materials 必须是非空 array")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ValidatorMutationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
