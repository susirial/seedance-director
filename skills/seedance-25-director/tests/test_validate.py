"""Offline contract tests; all fixtures stay in temporary directories."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate.py"


class ValidatorTests(unittest.TestCase):
    def invoke(self, *args):
        self.assertTrue(SCRIPT.is_file(), "Offline validator is not implemented")
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *map(str, args)],
            capture_output=True, text=True, timeout=20,
        )

    def test_cli_help(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("package", result.stdout)
        self.assertIn("skill", result.stdout)

    def example(self, name="product"):
        return json.loads((ROOT / "assets" / "examples" /
                           f"{name}-package.json").read_text())

    def check_package(self, data, expected=0, field=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "package.json"
            path.write_text(json.dumps(data, ensure_ascii=False))
            (Path(folder) / "fixture.dat").write_text("metadata-only test fixture")
            result = self.invoke("package", path)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        if field:
            self.assertIn(field, result.stdout)
        return result

    def test_examples_and_draft_template(self):
        for name in ("narrative", "product", "animation"):
            with self.subTest(name=name):
                result = self.check_package(self.example(name))
                self.assertIn("WARNING", result.stdout)
        template = json.loads((ROOT / "assets" /
                               "production-package.template.json").read_text())
        self.assertIn("WARNING", self.check_package(template).stdout)

    def test_read_and_argument_errors(self):
        for args in (("package", "/nonexistent/package.json"), ("bad-mode", ".")):
            with self.subTest(args=args):
                self.assertEqual(self.invoke(*args).returncode, 2)

    def test_strict_json(self):
        for text in ('{"schema_version":1,"schema_version":1}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e400}', '{'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "bad.json"
                path.write_text(text)
                result = self.invoke("package", path)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("ERROR", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_structural_mutations(self):
        cases = [
            (("schema_version",), True),
            (("project", "title"), ""),
            (("project", "stage"), "ready"),
            (("project", "total_seconds"), True),
            (("project", "aspect_ratio"), "0:9"),
            (("project", "model_line"), "seedance-2.0"),
            (("project", "surface", "verified"), "yes"),
            (("assets", 0, "media_type"), "pdf"),
            (("assets", 0, "duration_seconds"), 3),
            (("assets", 0, "width"), True),
            (("assets", 0, "observation"), "guessed"),
            (("sources", 0, "provenance"), "guessed"),
            (("scenes", 0, "geography"), ""),
            (("shots", 0, "contract", "camera"), ""),
            (("shots", 0, "checks"), ["one"]),
            (("shots", 0, "representative"), 1),
            (("shots", 0, "rejected_option"), ""),
            (("keyframes", 0, "image_prompt_en"), ""),
            (("clips", 0, "duration_seconds"), True),
            (("clips", 0, "status"), "generated"),
            (("clips", 0, "bindings"), "not-an-array"),
            (("review", "media_tested"), True),
            (("review", "issues", 0, "level"), "critical"),
        ]
        for keys, value in cases:
            with self.subTest(keys=keys):
                data = self.example()
                target = data
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                self.check_package(data, 1, str(keys[-1]))
        for key in self.example():
            with self.subTest(missing=key):
                data = self.example()
                del data[key]
                self.check_package(data, 1, key)
        for malformed in (None, [], {"project": 8}):
            self.check_package(malformed, 1)

    def test_id_references_and_style(self):
        mutations = [
            (("assets", 1, "id"), "A001"),
            (("assets", 0, "id"), "bad"),
            (("scenes", 0, "source_ids"), ["SRC999"]),
            (("shots", 0, "scene_id"), "SC999"),
            (("shots", 0, "source_ids"), []),
            (("shots", 0, "keyframe_ids"), []),
            (("keyframes", 0, "shot_id"), "SH999"),
            (("keyframes", 0, "output_asset_id"), "A999"),
            (("style", "components", "media"), "look.natural"),
            (("style", "preset_id"), "preset.missing"),
            (("style", "secondary_look"), "media.pixel"),
            (("style", "overrides"), []),
            (("style", "exceptions"), [{"shot_id": "SH999", "reason": "test"}]),
            (("review", "issues", 0, "object_id"), "SH999"),
        ]
        for keys, value in mutations:
            with self.subTest(keys=keys):
                data = self.example()
                target = data
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                self.check_package(data, 1)
        data = self.example()
        data["adaptation_notes"] = [{
            "id": "AD001", "source_id": "SRC001", "change": "new fact",
            "reason": "test", "status": "proposed", "applied": True,
        }]
        self.check_package(data, 1, "applied")
        data["adaptation_notes"][0]["status"] = "approved"
        self.check_package(data)

    def test_media_paths_and_states(self):
        for path in ("/tmp/outside.png", "../outside.png",
                     "https://example.com/a.png", "missing.png"):
            with self.subTest(path=path):
                data = self.example()
                data["assets"][0].update(status="available", path=path)
                self.check_package(data, 1, "path")
        data = self.example()
        data["assets"][0].update(status="accepted", path="fixture.dat")
        self.check_package(data, 1, "observation")
        data["assets"][0]["observation"] = "user_reported"
        self.check_package(data)
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            outside = base / "outside.dat"
            outside.write_text("external")
            inside = base / "package"
            inside.mkdir()
            (inside / "escape.dat").symlink_to(outside)
            data["assets"][0]["path"] = "escape.dat"
            path = inside / "package.json"
            path.write_text(json.dumps(data))
            result = self.invoke("package", path)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("path", result.stdout)

    def test_skill_library_and_custom_cards(self):
        self.assertEqual(self.invoke("skill", ROOT).returncode, 0)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            custom = root / "assets" / "styles" / "custom.json"
            card = json.loads((root / "assets" / "style-card.template.json").read_text())
            component = json.loads((root / "assets" / "styles" /
                                    "media.json").read_text())[0]
            component["id"] = "custom.camera-medium"
            card["components"]["media"] = component["id"]
            custom.write_text(json.dumps([component, card]))
            self.assertEqual(self.invoke("skill", root).returncode, 0)
            for value in ([card, card], [{"kind": "preset", "id": "custom.empty"}],
                          [dict(component, axis="new-axis")],
                          [dict(component, id="media.photographic")],
                          [dict(card, components={"media": "missing"})]):
                with self.subTest(value=value):
                    custom.write_text(json.dumps(value))
                    result = self.invoke("skill", root)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertNotIn("Traceback", result.stderr)

    def test_skill_frontmatter_links_and_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            entry = root / "SKILL.md"
            original = entry.read_text()
            changes = (
                original.replace("name: seedance-25-director", "name: wrong-name"),
                original.replace("description: ", 'description: "'),
                original + "\n[missing](references/missing.md)\n",
                original + "\n[escape](../outside.md)\n",
                original + "\n[anchor](references/worked-examples.md#absent)\n",
                original + "\n" * 500,
            )
            for value in changes:
                with self.subTest(value=value[-90:]):
                    entry.write_text(value)
                    result = self.invoke("skill", root)
                    self.assertEqual(result.returncode, 1, result.stdout)
            entry.write_text(original)
            path = root / "assets" / "styles" / "presets" / "live-action.json"
            cards = json.loads(path.read_text())
            path.write_text(json.dumps(cards[:-1]))
            self.assertEqual(self.invoke("skill", root).returncode, 1)

    def prepared(self, data=None):
        data = copy.deepcopy(data or self.example())
        data["project"]["stage"] = "confirmed"
        data["style"]["confirmed"] = True
        data["project"]["surface"].update(
            name="Metadata fixture, not an integration claim", verified=True,
            source="https://www.volcengine.com/docs/82379/2607689",
            checked_at="2026-10-04", operations=["reference_to_video"],
        )
        for asset in data["assets"]:
            asset.update(status="accepted", observation="user_reported",
                         path="fixture.dat", width=1280, height=720)
        for clip in data["clips"]:
            clip["status"] = "prepared"
        return data

    def test_prepared_requirements(self):
        self.check_package(self.prepared())
        cases = [
            (("style", "confirmed"), False),
            (("style", "components", "media"), None),
            (("project", "surface", "verified"), False),
            (("project", "surface", "source"), None),
            (("project", "surface", "checked_at"), "2026-02-31"),
            (("project", "surface", "operations"), ["edit"]),
            (("assets", 1, "status"), "planned"),
            (("assets", 1, "status"), "rejected"),
            (("assets", 1, "width"), None),
        ]
        for keys, value in cases:
            with self.subTest(keys=keys):
                data = self.prepared()
                target = data
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                self.check_package(data, 1)
        data = self.prepared(self.example("narrative"))
        data["clips"][0]["status"] = "provisional"
        self.check_package(data, 1, "depends_on")

    def test_timeline_and_duration(self):
        for intervals in ([(1, 8)], [(0, 3), (4, 8)], [(0, 5), (4, 8)],
                          [(0, 5), (5, 4)], [(0, 9)], [(0, 7)], []):
            with self.subTest(intervals=intervals):
                data = self.example()
                data["clips"][0]["timeline"] = [
                    {"shot_id": "SH001", "start": start, "end": end}
                    for start, end in intervals]
                self.check_package(data, 1, "timeline")
        for duration in (0, -1, True, 8.5, 31):
            data = self.example()
            data["clips"][0]["duration_seconds"] = duration
            self.check_package(data, 1, "duration_seconds")
        data = self.example()
        data["project"]["total_seconds"] = 9
        self.check_package(data, 1, "total_seconds")
        data = self.example("narrative")
        clip = data["clips"][0]
        clip.update(shot_ids=["SH001", "SH002"], duration_seconds=14,
                    timeline=[{"shot_id": "SH001", "start": 0, "end": 8},
                              {"shot_id": "SH002", "start": 8, "end": 14}])
        data["clips"] = [clip]
        data["review"]["issues"] = []
        self.check_package(data)
        clip["shot_ids"].reverse()
        self.check_package(data, 1, "timeline")

    def test_bindings(self):
        for key, value in (("token", "@图片2"), ("token", "@视频1"),
                           ("asset_id", "A999"), ("dimensions", []), ("exclude", [])):
            with self.subTest(key=key, value=value):
                data = self.example()
                data["clips"][0]["bindings"][0][key] = value
                self.check_package(data, 1, "bindings")
        data = self.example()
        data["clips"][0]["video_prompt_zh"] += " @音频1"
        self.check_package(data, 1, "video_prompt_zh")
        data = self.example()
        binding = copy.deepcopy(data["clips"][0]["bindings"][0])
        binding.update(token="@图片2", asset_id="A001")
        data["clips"][0]["bindings"].append(binding)
        self.check_package(data, 1, "dimensions")
        binding["target"] = "different target"
        self.check_package(data)
        binding["asset_id"] = "A002"
        self.check_package(data, 1, "asset_id")
        for task, bindings in (("text_to_video", self.example()["clips"][0]["bindings"]),
                               ("reference_to_video", [])):
            data = self.example()
            data["clips"][0].update(task=task, bindings=bindings,
                                    video_prompt_zh="Static view without media tokens")
            self.check_package(data, 1, "bindings")
        data["clips"][0]["task"] = "text_to_video"
        self.check_package(data)

    def capacity_data(self, images=0, videos=0, audios=0, seconds=1):
        data = self.example()
        clip = data["clips"][0]
        clip.update(bindings=[], video_prompt_zh="Metadata capacity fixture")
        counter = 100
        for media, count, token in (("image", images, "@图片"),
                                     ("video", videos, "@视频"), ("audio", audios, "@音频")):
            for number in range(1, count + 1):
                counter += 1
                asset = copy.deepcopy(data["assets"][0])
                asset.update(id=f"A{counter}", media_type=media,
                             duration_seconds=None if media == "image" else seconds)
                data["assets"].append(asset)
                clip["bindings"].append({
                    "token": token + str(number), "asset_id": asset["id"],
                    "target": asset["id"], "dimensions": ["reference"], "exclude": ["other"],
                })
        return data

    def test_capacity_boundaries(self):
        for counts, code in (((30, 10, 10), 0), ((31, 0, 0), 1),
                             ((0, 11, 0), 1), ((0, 0, 11), 1),
                             ((30, 10, 11), 1)):
            with self.subTest(counts=counts):
                self.check_package(self.capacity_data(*counts), code)
        for media in ("videos", "audios"):
            self.check_package(self.capacity_data(**{media: 10}, seconds=3))
            self.check_package(self.capacity_data(**{media: 10}, seconds=4), 1)
        data = self.prepared(self.capacity_data(videos=1))
        data["assets"][-1]["duration_seconds"] = None
        self.check_package(data, 1, "duration_seconds")
        data["clips"][0]["status"] = "provisional"
        self.check_package(data)
        data = self.prepared()
        for limits in ({"images": 0}, {"images": 31}, {"images": True}, {"unknown": 2}):
            data["project"]["surface"]["limits"] = limits
            self.check_package(data, 1, "limits")

    def test_keyframe_and_clip_cycles(self):
        data = self.example()
        data["keyframes"][0]["depends_on"] = ["A002"]
        self.check_package(data, 1, "depends_on")
        data = self.example()
        other = copy.deepcopy(data["keyframes"][0])
        other.update(id="KF002", output_asset_id="A001", depends_on=["A002"])
        data["keyframes"].append(other)
        data["shots"][0]["keyframe_ids"].append("KF002")
        self.check_package(data, 1, "depends_on")
        other.update(output_asset_id="A002", depends_on=["A001"])
        self.check_package(data, 1, "output_asset_id")
        data = self.example("narrative")
        data["clips"][0]["depends_on"] = ["CL002"]
        self.check_package(data, 1, "depends_on")
        data["clips"][0]["depends_on"] = ["CL999"]
        self.check_package(data, 1, "depends_on")

    def test_first_last_frames(self):
        data = self.example()
        clip = data["clips"][0]
        clip["task"] = "image_to_video"
        self.check_package(data, 1, "first_frame_id")
        clip["first_frame_id"] = "A002"
        self.check_package(data)
        clip["task"] = "first_last_frame"
        self.check_package(data, 1, "last_frame_id")
        clip["last_frame_id"] = "A001"
        self.check_package(data, 1, "bindings")
        clip["bindings"].append({"token": "@图片2", "asset_id": "A001", "target": "end",
                                 "dimensions": ["end"], "exclude": ["start"]})
        self.check_package(data)
        for asset in data["assets"]:
            asset.update(width=1280, height=720)
        self.check_package(data)
        data["assets"][0].update(width=720, height=1280)
        self.check_package(data, 1, "aspect_ratio")
        data = self.example()
        data["clips"][0]["first_frame_id"] = "A002"
        self.check_package(data, 1, "first_frame_id")

    def source_task(self, task):
        data = self.example()
        source = copy.deepcopy(data["assets"][0])
        source.update(id="A003", media_type="video", duration_seconds=8,
                      width=1280, height=720, status="accepted",
                      path="fixture.dat", observation="user_reported")
        data["assets"].append(source)
        clip = data["clips"][0]
        clip.update(task=task, source_video_id="A003", bindings=[{
            "token": "@视频1", "asset_id": "A003", "target": "source",
            "dimensions": ["motion"], "exclude": ["new content"],
        }], video_prompt_zh="@视频1 metadata test")
        if task == "edit":
            clip.update(edit_range={"start": 1, "end": 3}, edit_change="old to new")
        else:
            clip["extension_depth"] = 1
        return data

    def test_edit_and_extend(self):
        for task in ("edit", "extend"):
            data = self.source_task(task)
            self.check_package(data)
            for field, value in (("source_video_id", None), ("source_video_id", "A001")):
                broken = copy.deepcopy(data)
                broken["clips"][0][field] = value
                self.check_package(broken, 1, field)
        data = self.source_task("edit")
        for interval in ({"start": 0, "end": 9}, {"start": 5, "end": 3}, None):
            data["clips"][0]["edit_range"] = interval
            self.check_package(data, 1, "edit_range")
        data = self.source_task("edit")
        data["assets"][-1]["duration_seconds"] = 10
        self.check_package(data, 1, "duration_seconds")
        data = self.source_task("edit")
        data["assets"][-1].update(width=720, height=1280)
        self.check_package(data, 1, "aspect_ratio")
        data = self.source_task("extend")
        for depth in (3, True, 0):
            data["clips"][0]["extension_depth"] = depth
            self.check_package(data, 1, "extension_depth")
        data["clips"][0]["extension_depth"] = None
        self.check_package(data)
        data["assets"][-1]["status"] = "available"
        self.check_package(data, 1, "source_video_id")

    def test_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            before = {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
            self.assertEqual(self.invoke("skill", root).returncode, 0)
            after = {str(p.relative_to(root)): p.read_bytes()
                     for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_incomplete_dimensions_do_not_crash(self):
        data = self.example()
        data["clips"][0].update(task="image_to_video", first_frame_id="A002")
        data["assets"][1].update(width=1280, height=None)
        self.check_package(data, 1)

    def test_source_chain_and_frame_ratio(self):
        with self.subTest("source chain"):
            data = self.example()
            data["sources"].append(dict(data["sources"][0], id="SRC002"))
            data["shots"][0]["source_ids"] = ["SRC002"]
            self.check_package(data, 1, "source_ids")
        with self.subTest("frame ratio"):
            data = self.example()
            data["keyframes"][0]["aspect_ratio"] = "9:16"
            self.check_package(data, 1, "aspect_ratio")
        with self.subTest("partial style"):
            data = self.example()
            data["style"]["components"]["media"] = None
            self.check_package(data, 1, "components")

    def test_overflow_in_otherwise_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "package.json"
            text = json.dumps(self.example())
            path.write_text(text[:-1] + ', "extra":1e400}')
            self.assertEqual(self.invoke("package", path).returncode, 1)

    def test_valid_prepared_task_routes(self):
        for task in ("text_to_video", "image_to_video", "first_last_frame", "edit", "extend"):
            with self.subTest(task=task):
                base = self.source_task(task) if task in ("edit", "extend") else self.example()
                data = self.prepared(base)
                data["project"]["surface"]["operations"] = [task]
                clip = data["clips"][0]
                clip["task"] = task
                if task == "text_to_video":
                    clip.update(bindings=[], video_prompt_zh="No input media")
                elif task in ("image_to_video", "first_last_frame"):
                    clip["first_frame_id"] = "A002"
                    if task == "first_last_frame":
                        clip["last_frame_id"] = "A001"
                        clip["bindings"].append({
                            "token": "@图片2", "asset_id": "A001", "target": "end",
                            "dimensions": ["end"], "exclude": ["start"],
                        })
                self.check_package(data)
                if task == "extend":
                    clip["extension_depth"] = None
                    self.check_package(data, 1, "extension_depth")

    def test_preset_example_binding_and_duration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            path = root / "assets/styles/presets/live-action.json"
            original = json.loads(path.read_text())
            for key, value in (("duration_seconds", 31),
                               ("video_prompt_zh", "@图片9 undefined"),
                               ("bindings", [])):
                with self.subTest(key=key):
                    cards = copy.deepcopy(original)
                    cards[0]["example"][key] = value
                    path.write_text(json.dumps(cards))
                    self.assertEqual(self.invoke("skill", root).returncode, 1)

    def test_skill_profile_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            path = root / "assets/seedance-25-profile.json"
            original = json.loads(path.read_text())
            for value in ({}, dict(original, checked_at="not-a-date"),
                          dict(original, limits={"images": True})):
                path.write_text(json.dumps(value))
                result = self.invoke("skill", root)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_skill_asset_symlink_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            target = root / "assets/styles/media.json"
            external = Path(folder) / "outside.json"
            external.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(external)
            result = self.invoke("skill", root)
            self.assertEqual(result.returncode, 1, result.stdout)

    def test_requested_prompt_preset_categories(self):
        path = ROOT / "assets" / "styles" / "prompt-presets.json"
        self.assertTrue(path.is_file(), "预制风格提示词库尚未创建")
        data = json.loads(path.read_text())
        expected = {
            "live-action-realistic", "animation-3d", "anime-2d",
            "photographic-art", "illustration-art", "punk-art",
            "traditional-fine-art", "craft-art",
        }
        self.assertEqual({item["id"] for item in data["categories"]}, expected)
        for category in data["categories"]:
            self.assertGreaterEqual(len(category["presets"]), 4)
            for preset in category["presets"]:
                self.assertIn("{subject}", preset["image_prompt_en"])
                self.assertIn("{scene}", preset["image_prompt_en"])
                self.assertIn("{action}", preset["video_prompt_zh"])
        live_names = {
            item["name"] for item in data["categories"][0]["presets"]
        }
        self.assertTrue({
            "人像写实", "古风写实", "古代战场", "现代都市",
            "玄幻修仙", "悬疑恐怖", "未来科幻", "中式梦境",
            "国风古典", "年代剧", "伪纪录片", "中世纪奇幻",
            "古风武侠", "邵氏电影", "民国剧", "惊悚压抑",
            "暗黑哥特", "中式华丽",
        } <= live_names)

    def test_skill_rejects_incomplete_prompt_preset(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / ROOT.name
            shutil.copytree(ROOT, root)
            path = root / "assets" / "styles" / "prompt-presets.json"
            data = json.loads(path.read_text())
            data["categories"][0]["presets"][0]["image_prompt_en"] = "empty style"
            path.write_text(json.dumps(data))
            result = self.invoke("skill", root)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("image_prompt_en", result.stdout)

    def test_skill_entry_links_prompt_presets(self):
        entry = (ROOT / "SKILL.md").read_text()
        self.assertIn("assets/styles/prompt-presets.json", entry)
        self.assertIn("references/style-prompt-presets.md", entry)


if __name__ == "__main__":
    unittest.main()
