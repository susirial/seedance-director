"""Read-only, standard-library validator for Seedance director packages."""

import argparse
from datetime import date
from fractions import Fraction
import json
import math
from pathlib import Path, PureWindowsPath
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
TASKS = ("text_to_video", "image_to_video", "reference_to_video",
         "first_last_frame", "edit", "extend")
AXES = {"media": 8, "look": 12, "direction": 6, "purpose": 10}
FAMILIES = {"live-action": 8, "animation-2d": 6, "animation-3d": 4,
            "art-handmade": 6, "commercial-design": 6}


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def require(self, condition, path, message, suggestion="Follow output-contract.md"):
        if not condition:
            self.errors += 1
            print(f"ERROR {path}: {message}; fix: {suggestion}")
        return bool(condition)

    def warn(self, path, message):
        self.warnings += 1
        print(f"WARNING {path}: {message}; next: confirm before submission")


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"non-finite JSON value: {value}")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            constant(value)
        return number

    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=pairs, parse_constant=constant,
                      parse_float=finite_float)


def fields(names, spec="text"):
    return dict.fromkeys(names.split(), spec)


def shape(value, spec, path, report):
    """Validate types before semantic checks so malformed input cannot crash them."""
    if isinstance(spec, dict):
        if not report.require(isinstance(value, dict), path, "expected object"):
            return False
        valid = True
        if isinstance(value.get("id"), str):
            path += f"({value['id']})"
        for key, child in spec.items():
            optional = key.endswith("?")
            name = key.rstrip("?")
            if name not in value:
                if not optional:
                    report.require(False, path + "." + name, "missing required field")
                    valid = False
            elif not shape(value[name], child, path + "." + name, report):
                valid = False
        return valid
    if isinstance(spec, list):
        if not report.require(isinstance(value, list), path, "expected array"):
            return False
        results = [shape(item, spec[0], f"{path}[{i}]", report)
                   for i, item in enumerate(value)]
        return all(results)
    if isinstance(spec, tuple):
        return report.require(type(value) is str and value in spec, path,
                              f"expected one of {spec}")
    if spec.endswith("?"):
        return value is None or shape(value, spec[:-1], path, report)
    if spec == "range":
        return shape(value, {"start": "seconds", "end": "positive"}, path, report)
    checks = {
        "text": lambda: isinstance(value, str) and bool(value.strip()),
        "string": lambda: isinstance(value, str),
        "bool": lambda: type(value) is bool,
        "positive": lambda: type(value) is int and value > 0,
        "seconds": lambda: type(value) is int and value >= 0,
        "version": lambda: type(value) is int and value == 1,
        "ratio": lambda: isinstance(value, str) and
        re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", value),
    }
    return report.require(checks[spec](), path, f"expected {spec}")


COMPONENT = {
    **fields("id name description compatibility_notes"), "kind": ("component",),
    "axis": tuple(AXES), "aliases": ["text"], "rules": ["text"],
}
EXAMPLE = {
    **fields("source director_intent shot_reason image_prompt_en image_prompt_zh "
             "end_state video_prompt_zh fallback"),
    **{key: ["text"] for key in ("invariants", "references", "checks")},
    "duration_seconds": "positive", "aspect_ratio": "ratio", "task": TASKS,
    "bindings": [fields("token role")], "status": ("planned",),
    "media_tested": "bool",
}
PRESET = {
    **fields("id name description character_design environment_design visual_rules "
             "motion_rules sound_rules performance_rules origin"),
    "kind": ("preset",), "family": tuple(FAMILIES),
    "aliases": ["text"], "components": fields("media look direction purpose"),
    **{key: ["text"] for key in ("suitable_for", "avoid_when", "continuity_anchors",
                                "failure_modes")}, "example": EXAMPLE,
}
BINDING = {**fields("token asset_id target"), "dimensions": ["text"], "exclude": ["text"]}
CLIP = {
    **fields("id video_prompt_zh fallback"), "task": TASKS,
    "shot_ids": ["text"], "duration_seconds": "positive", "aspect_ratio": "ratio",
    "timeline": [{"shot_id": "text", "start": "seconds", "end": "positive"}],
    "bindings": [BINDING],
    **fields("first_frame_id last_frame_id source_video_id edit_change source_clip_id",
             "text?"),
    "edit_range": "range?", "preserve": ["text"], "extension_depth": "positive?",
    "status": ("provisional", "prepared"), "depends_on": ["text"],
}
# The nullable range is handled by the same structural validator.
PACKAGE = {
    "schema_version": "version",
    "project": {
        **fields("id title purpose audience language"), "total_seconds": "positive?",
        "aspect_ratio": "ratio?", "stage": ("draft", "confirmed"),
        "model_line": ("seedance-2.5",),
        "surface": {**fields("name source checked_at", "text?"), "verified": "bool",
                    "operations": [TASKS]},
    },
    "sources": [{**fields("id locator excerpt"), "type": ("script", "copy", "storyboard", "text"),
                 "provenance": ("user_text", "authored", "user_reported", "observed")}],
    "adaptation_notes": [{**fields("id source_id change reason"),
                          "status": ("proposed", "approved", "rejected"), "applied": "bool"}],
    "style": {
        "preset_id": "text?", "components": fields("media look direction purpose", "text?"),
        "secondary_look": "text?", "rationale": "text", "confirmed": "bool",
        "overrides": ["text"], "exceptions": [fields("shot_id reason")],
    },
    "assets": [{
        **fields("id role rights state_description"), "media_type": ("image", "video", "audio"),
        "status": ("planned", "available", "accepted", "rejected"), "path": "text?",
        "duration_seconds": "positive?", "width": "positive?", "height": "positive?",
        "observation": ("planned", "user_reported", "observed"),
        "design_prompt_en?": "text", "design_notes_zh?": "text",
    }],
    "scenes": [{**fields("id location time geography intent"),
                "source_ids": ["text"], "characters": ["text"]}],
    "shots": [{
        **fields("id scene_id audience_task pov reason start_state end_state action edit_relation"),
        "source_ids": ["text"], "keyframe_ids": ["text"], "checks": ["text"],
        "contract": fields("size perspective composition lighting camera blocking fragile"),
        "sound": fields("dialogue ambience effects music"),
        "representative": "bool", "rejected_option": "string",
    }],
    "keyframes": [{
        **fields("id shot_id output_asset_id image_prompt_en image_prompt_zh"),
        "role": ("start", "end", "intermediate"), "depends_on": ["text"],
        "aspect_ratio": "ratio", "checks": ["text"],
    }],
    "clips": [CLIP],
    "review": {
        "media_tested": "bool", "test_evidence?": "text",
        "issues": [{**fields("id object_id evidence suggestion"),
                    "level": ("error", "warning", "info"), "status": ("open", "resolved")}],
    },
}


def resolve_inside(base, text, allow_parent=False):
    parsed = urlsplit(text)
    path = Path(text)
    if (parsed.scheme or parsed.netloc or path.is_absolute() or
            PureWindowsPath(text).is_absolute() or "\\" in text or
            (not allow_parent and ".." in path.parts)):
        raise ValueError("use a relative in-package path")
    resolved = (base / path).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError("path escapes package, including symlinks")
    return resolved


def validate_components(components, library, path, report, nullable=False):
    for axis, value in components.items():
        if value is None and nullable:
            continue
        card = library.get(value, {})
        report.require(card.get("kind") == "component" and card.get("axis") == axis,
                       f"{path}.{axis}", "unknown component or incorrect axis")


def load_library(root, report):
    library = {}
    collections = [(root / "assets/styles" / f"{axis}.json", count, axis)
                   for axis, count in AXES.items()]
    collections += [(root / "assets/styles/presets" / f"{family}.json", count, family)
                    for family, count in FAMILIES.items()]
    collections.append((root / "assets/styles/custom.json", None, "custom"))
    for path, count, group in collections:
        if not report.require(path.resolve().is_relative_to(root), str(path),
                              "style file escapes skill root"):
            continue
        cards = load_json(path)
        if not report.require(isinstance(cards, list), str(path), "expected array"):
            continue
        if count is not None:
            report.require(len(cards) == count, str(path), f"expected {count} built-in cards")
        for i, card in enumerate(cards):
            location = f"{path.name}[{i}]"
            if not isinstance(card, dict):
                report.require(False, location, "expected card object")
                continue
            spec = COMPONENT if card.get("kind") == "component" else PRESET
            if not shape(card, spec, location, report):
                continue
            cid = card["id"]
            prefix = "custom" if group == "custom" else (
                group if group in AXES else "preset")
            report.require(bool(re.fullmatch(re.escape(prefix) + r"\.[a-z0-9]+(?:-[a-z0-9]+)*",
                                            cid)), location + ".id", "invalid ID namespace")
            report.require(cid not in library, location + ".id", "duplicate style ID")
            if group in AXES:
                report.require(card.get("axis") == group, location, "wrong component axis")
            elif group in FAMILIES:
                report.require(card.get("family") == group, location, "wrong preset family")
            library[cid] = card
    for cid, card in library.items():
        if card["kind"] == "component":
            report.require(bool(card["rules"]), cid + ".rules", "rules cannot be empty")
        else:
            validate_preset(card, library, cid, report)
    return library


def validate_preset(card, library, path, report):
    validate_components(card["components"], library, path + ".components", report)
    for key in ("suitable_for", "avoid_when", "continuity_anchors", "failure_modes"):
        report.require(bool(card[key]), path + "." + key, "expected nonempty list")
    example = card["example"]
    report.require(len(example["checks"]) >= 5, path + ".example.checks",
                   "need at least five observable checks")
    for key in ("references", "invariants"):
        report.require(bool(example[key]), path + ".example." + key, "expected nonempty list")
    report.require(not example["media_tested"], path + ".example.media_tested",
                   "built-in examples are untested designs")
    report.require(example["duration_seconds"] <= 30, path + ".example.duration_seconds",
                   "micro-example exceeds documented new generation duration")
    tokens = [binding["token"] for binding in example["bindings"]]
    counts = dict.fromkeys(TOKEN_NAMES.values(), 0)
    for token in tokens:
        match = re.fullmatch(r"@(" + "|".join(counts) + r")([1-9][0-9]*)", token)
        if report.require(match is not None, path + ".example.bindings", "invalid upload label"):
            media, number = match.groups()
            counts[media] += 1
            report.require(int(number) == counts[media], path + ".example.bindings",
                           "upload labels must be contiguous")
    report.require(set(TOKEN_RE.findall(example["video_prompt_zh"])) <= set(tokens),
                   path + ".example.video_prompt_zh", "undefined media label")
    report.require(example["task"] == "reference_to_video" and bool(tokens),
                   path + ".example.bindings",
                   "micro-example format requires reference inputs; use a full package for other tasks")


def ref(value, index, path, report):
    return report.require(value in index, path, f"unresolved reference {value}")


def refs(values, index, path, report, required=False):
    report.require(len(values) == len(set(values)), path, "duplicate references")
    if required:
        report.require(bool(values), path, "at least one reference required")
    for value in values:
        ref(value, index, path, report)


def validate_package(data, base, library, report, profile=None):
    if not shape(data, PACKAGE, "$", report):
        return
    project, style = data["project"], data["style"]
    if profile is None:
        profile = load_json(ROOT / "assets/seedance-25-profile.json")
    if not validate_profile(profile, report):
        return
    report.warn("$.project.stage", "structure-only check; no media generation or quality test")
    if project["stage"] == "draft":
        report.warn("$.project", "draft decisions and resources may be incomplete")
    groups = ("sources", "adaptation_notes", "assets", "scenes", "shots", "keyframes", "clips")
    prefixes = ("SRC", "AD", "A", "SC", "SH", "KF", "CL")
    indexes, all_ids = {}, set()
    for group, prefix in zip(groups, prefixes):
        indexes[group] = {}
        for item in data[group]:
            cid = item["id"]
            path = f"$.{group}({cid})"
            report.require(bool(re.fullmatch(prefix + r"[0-9]{3,}", cid)), path + ".id",
                           f"expected {prefix} plus at least three digits")
            report.require(cid not in all_ids, path + ".id", "duplicate entity ID")
            all_ids.add(cid)
            indexes[group][cid] = item
    assets, shots = indexes["assets"], indexes["shots"]
    validate_components(style["components"], library, "$.style.components", report, True)
    values = list(style["components"].values())
    report.require(all(value is None for value in values) or all(value is not None for value in values),
                   "$.style.components", "select all four components or leave all null in a draft")
    preset = library.get(style["preset_id"])
    if style["preset_id"] is not None:
        report.require(preset is not None and preset.get("kind") == "preset",
                       "$.style.preset_id", "unknown preset")
        if preset and preset.get("components") != style["components"]:
            report.require(bool(style["overrides"]), "$.style.overrides",
                           "explain departures from the selected preset")
    if style["secondary_look"] is not None:
        validate_components({"look": style["secondary_look"]}, library,
                            "$.style.secondary_look", report)
    for item in style["exceptions"]:
        ref(item["shot_id"], shots, "$.style.exceptions.shot_id", report)
    for note in data["adaptation_notes"]:
        path = f"$.adaptation_notes({note['id']})"
        ref(note["source_id"], indexes["sources"], path + ".source_id", report)
        report.require(not note["applied"] or note["status"] == "approved",
                       path + ".applied", "applied changes require approval")
    for asset in data["assets"]:
        path = f"$.assets({asset['id']})"
        if asset["path"] is not None:
            try:
                resolved = resolve_inside(base, asset["path"])
                if asset["status"] != "planned":
                    report.require(resolved.is_file(), path + ".path", "media file not found")
            except (ValueError, OSError, RuntimeError) as exc:
                report.require(False, path + ".path", str(exc))
        else:
            report.require(asset["status"] == "planned", path + ".path",
                           "non-planned assets need an existing file")
        if asset["status"] == "accepted":
            report.require(asset["observation"] != "planned", path + ".observation",
                           "accepted media needs observed or user-reported evidence")
        if asset["media_type"] == "image":
            report.require(asset["duration_seconds"] is None, path + ".duration_seconds",
                           "still images have no duration")
        if asset["media_type"] == "audio":
            report.require(asset["width"] is None and asset["height"] is None,
                           path + ".width", "audio has no dimensions")
        else:
            report.require((asset["width"] is None) == (asset["height"] is None),
                           path + ".width", "width and height must both be known or null")
    for scene in data["scenes"]:
        refs(scene["source_ids"], indexes["sources"], f"$.scenes({scene['id']}).source_ids",
             report, True)
    for shot in data["shots"]:
        path = f"$.shots({shot['id']})"
        ref(shot["scene_id"], indexes["scenes"], path + ".scene_id", report)
        refs(shot["source_ids"], indexes["sources"], path + ".source_ids", report, True)
        scene = indexes["scenes"].get(shot["scene_id"])
        if scene:
            report.require(set(shot["source_ids"]) <= set(scene["source_ids"]),
                           path + ".source_ids", "shot sources must be included in its scene")
        refs(shot["keyframe_ids"], indexes["keyframes"], path + ".keyframe_ids", report)
        actual = {k["id"] for k in data["keyframes"] if k["shot_id"] == shot["id"]}
        report.require(set(shot["keyframe_ids"]) == actual, path + ".keyframe_ids",
                       "shot and keyframe references must agree in both directions")
        report.require(len(shot["checks"]) >= (5 if shot["representative"] else 1),
                       path + ".checks", "insufficient observable checks")
        if shot["representative"]:
            report.require(bool(shot["rejected_option"].strip()), path + ".rejected_option",
                           "representative shots need a rejected alternative and reason")
    for frame in data["keyframes"]:
        path = f"$.keyframes({frame['id']})"
        ref(frame["shot_id"], shots, path + ".shot_id", report)
        ref(frame["output_asset_id"], assets, path + ".output_asset_id", report)
        report.require(assets.get(frame["output_asset_id"], {}).get("media_type") == "image",
                       path + ".output_asset_id", "keyframe output must be an image")
        refs(frame["depends_on"], assets, path + ".depends_on", report)
        report.require(bool(frame["checks"]), path + ".checks", "checks cannot be empty")
        if project["aspect_ratio"]:
            report.require(ratio(frame["aspect_ratio"]) == ratio(project["aspect_ratio"]),
                           path + ".aspect_ratio", "keyframe and project ratio must agree")
    outputs = [frame["output_asset_id"] for frame in data["keyframes"]]
    report.require(len(outputs) == len(set(outputs)), "$.keyframes.output_asset_id",
                   "each keyframe needs a distinct output")
    acyclic({frame["output_asset_id"]: frame["depends_on"] for frame in data["keyframes"]},
            "$.keyframes.depends_on", report)
    validate_tasks(data, indexes, profile, report)
    review = data["review"]
    if review["media_tested"]:
        report.require(bool(review.get("test_evidence")), "$.review.media_tested",
                       "test_evidence required; tool cannot verify its truth")
    for issue in review["issues"]:
        path = f"$.review.issues({issue['id']})"
        report.require(bool(re.fullmatch(r"R[0-9]{3,}", issue["id"])),
                       path + ".id", "expected R plus at least three digits")
        report.require(issue["id"] not in all_ids, path + ".id", "duplicate entity ID")
        all_ids.add(issue["id"])
        ref(issue["object_id"], all_ids | {project["id"]}, path + ".object_id", report)


def acyclic(graph, path, report):
    remaining = {key: set(value) & graph.keys() for key, value in graph.items()}
    while remaining:
        ready = {key for key, deps in remaining.items() if not deps}
        if not ready:
            report.require(False, path, "dependency cycle: " + ", ".join(sorted(remaining)))
            return
        remaining = {key: deps - ready for key, deps in remaining.items() if key not in ready}


def ratio(value):
    return Fraction(*map(int, value.split(":")))


def known(value, prepared, path, report):
    if value is not None:
        return True
    if prepared:
        report.require(False, path, "prepared task needs known metadata")
    else:
        report.warn(path, "unknown metadata in provisional task")
    return False


def match_ratio(asset, value, prepared, path, report):
    complete = asset["width"] if asset["height"] is not None else None
    if known(complete, prepared, path + ".aspect_ratio", report):
        report.require(Fraction(asset["width"], asset["height"]) == ratio(value),
                       path + ".aspect_ratio", "input and task aspect ratios differ")


def validate_surface(surface, limits, report):
    path = "$.project.surface"
    if surface["verified"]:
        for key in ("name", "source", "checked_at", "operations"):
            report.require(bool(surface[key]), path + "." + key, "verification evidence required")
        if surface["source"]:
            url = urlsplit(surface["source"])
            report.require(url.scheme == "https" and bool(url.netloc), path + ".source",
                           "expected official HTTPS evidence URL; verify publisher manually")
        try:
            date.fromisoformat(surface["checked_at"] or "")
        except ValueError:
            report.require(False, path + ".checked_at", "expected a valid ISO date")
    elif surface["operations"]:
        report.warn(path + ".operations", "operations listed but surface is not verified")
    effective = dict(limits)
    if "limits" in surface:
        overrides = surface["limits"]
        if report.require(isinstance(overrides, dict), path + ".limits", "expected object"):
            report.require(surface["verified"], path + ".limits", "overrides require evidence")
            for key, value in overrides.items():
                if report.require(key in limits and type(value) is int and
                                  0 <= value <= limits[key], path + ".limits." + key,
                                  "only stricter nonnegative integer limits are allowed"):
                    effective[key] = value
    return effective


def validate_profile(profile, report):
    spec = {
        "model_line": ("seedance-2.5",), "checked_at": "text",
        "sources": fields("model release guide"),
        "limits": fields("generation_seconds images videos audios total_assets "
                         "video_seconds audio_seconds", "positive"),
        "limit_source": ("model", "release", "guide"), "timestamp_unit_seconds": "positive",
        "extension": {**fields("model_page_wording release_wording note"),
                      "documented_depth": "positive"},
        "task_notes": fields("first_last_frame edit extend reference_to_video"),
        "unknown": ["text"], "boundary": "text",
    }
    path = "seedance-25-profile.json"
    if not shape(profile, spec, path, report):
        return False
    valid = True
    try:
        date.fromisoformat(profile["checked_at"])
    except ValueError:
        valid = report.require(False, path + ".checked_at", "expected valid ISO date")
    for key, source in profile["sources"].items():
        parsed = urlsplit(source)
        valid = report.require(parsed.scheme == "https" and bool(parsed.netloc),
                               path + ".sources." + key, "expected official HTTPS source") and valid
    return valid


def validate_prompt_presets(root, report):
    path = root / "assets/styles/prompt-presets.json"
    data = load_json(path)
    spec = {
        "schema_version": "version",
        "origin": "text",
        "usage": fields("image video rule"),
        "placeholders": fields(
            "subject scene pose composition lighting action camera sound "
            "end_state aspect_ratio"
        ),
        "categories": [{
            **fields("id name description"),
            "presets": [{
                **fields(
                    "id name image_prompt_en image_prompt_zh video_prompt_zh"
                ),
                "aliases": ["text"],
                "exclude": ["text"],
            }],
        }],
    }
    if not shape(data, spec, "prompt-presets.json", report):
        return
    expected = {
        "live-action-realistic", "animation-3d", "anime-2d",
        "photographic-art", "illustration-art", "punk-art",
        "traditional-fine-art", "craft-art",
    }
    category_ids = [item["id"] for item in data["categories"]]
    report.require(set(category_ids) == expected and
                   len(category_ids) == len(expected),
                   "prompt-presets.json.categories",
                   "expected the eight requested unique categories")
    preset_ids = set()
    for category in data["categories"]:
        cpath = f"prompt-presets.json.categories({category['id']})"
        report.require(len(category["presets"]) >= 4, cpath + ".presets",
                       "each category needs at least four usable presets")
        for preset in category["presets"]:
            ppath = f"{cpath}.presets({preset['id']})"
            report.require(
                bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+(?:-[a-z0-9]+)*",
                                  preset["id"])),
                ppath + ".id", "expected namespaced kebab-case preset ID"
            )
            report.require(preset["id"] not in preset_ids, ppath + ".id",
                           "duplicate prompt preset ID")
            preset_ids.add(preset["id"])
            for field, required in (
                ("image_prompt_en", ("{subject}", "{scene}", "{pose}",
                                     "{composition}", "{lighting}",
                                     "{aspect_ratio}")),
                ("video_prompt_zh", ("{action}", "{camera}", "{sound}",
                                     "{end_state}")),
            ):
                prompt = preset[field]
                report.require(all(slot in prompt for slot in required),
                               ppath + "." + field,
                               "missing required reusable prompt placeholders")
            report.require(bool(preset["exclude"]), ppath + ".exclude",
                           "exclude list cannot be empty")


TOKEN_NAMES = {"image": "\u56fe\u7247", "video": "\u89c6\u9891", "audio": "\u97f3\u9891"}
TOKEN_RE = re.compile(r"@(?:" + "|".join(TOKEN_NAMES.values()) + r")[0-9]+")


def validate_bindings(clip, assets, limits, report):
    path = f"$.clips({clip['id']}).bindings"
    prepared = clip["status"] == "prepared"
    counts = dict.fromkeys(TOKEN_NAMES, 0)
    durations = {"video": 0, "audio": 0}
    tokens, bound, owners = set(), set(), {}
    for binding in clip["bindings"]:
        bp = path + f"({binding['token']})"
        aid = binding["asset_id"]
        report.require(binding["token"] not in tokens, bp + ".token", "duplicate upload label")
        tokens.add(binding["token"])
        report.require(aid not in bound, bp + ".asset_id", "bind each asset once per task")
        bound.add(aid)
        report.require(bool(binding["dimensions"]) and bool(binding["exclude"]),
                       bp + ".dimensions", "dimensions and exclude must be nonempty")
        for dimension in binding["dimensions"]:
            key = (binding["target"], dimension)
            report.require(key not in owners or owners[key] == aid, bp + ".dimensions",
                           "two assets claim authority over the same target and dimension")
            owners[key] = aid
        if not ref(aid, assets, bp + ".asset_id", report):
            continue
        asset = assets[aid]
        media = asset["media_type"]
        counts[media] += 1
        expected = "@" + TOKEN_NAMES[media] + str(counts[media])
        report.require(binding["token"] == expected, bp + ".token",
                       f"media labels must be contiguous in upload order; expected {expected}")
        if prepared:
            report.require(asset["status"] in ("available", "accepted"), bp + ".asset_id",
                           "prepared task cannot use planned or rejected assets")
        if media in durations:
            if known(asset["duration_seconds"], prepared, bp + ".duration_seconds", report):
                durations[media] += asset["duration_seconds"]
        if media != "audio":
            known(asset["width"], prepared, bp + ".width", report)
    for media, count in counts.items():
        report.require(count <= limits[media + "s"], path, f"{media} count exceeds limits")
    report.require(len(bound) <= limits["total_assets"], path, "total_assets exceeds limits")
    for media, duration in durations.items():
        report.require(duration <= limits[media + "_seconds"], path + ".duration_seconds",
                       f"total {media} duration exceeds limits")
    report.require(set(TOKEN_RE.findall(clip["video_prompt_zh"])) <= tokens,
                   f"$.clips({clip['id']}).video_prompt_zh", "prompt has undefined media labels")
    return bound


def validate_tasks(data, indexes, profile, report):
    project, style = data["project"], data["style"]
    limits = validate_surface(project["surface"], profile["limits"], report)
    if project["stage"] == "confirmed":
        report.require(style["confirmed"] and all(style["components"].values()),
                       "$.style.confirmed", "confirmed project needs confirmed complete style")
        for group in ("sources", "scenes", "shots", "clips"):
            report.require(bool(data[group]), "$." + group, "confirmed project cannot be empty")
    assets = indexes["assets"]
    for clip in data["clips"]:
        path = f"$.clips({clip['id']})"
        prepared, task = clip["status"] == "prepared", clip["task"]
        refs(clip["shot_ids"], indexes["shots"], path + ".shot_ids", report, True)
        refs(clip["depends_on"], indexes["clips"], path + ".depends_on", report)
        if prepared:
            report.require(style["confirmed"] and all(style["components"].values()),
                           path + ".status", "prepared needs confirmed complete style")
            surface = project["surface"]
            report.require(surface["verified"] and task in surface["operations"],
                           path + ".status", "prepared needs a verified supporting surface")
            for dep in clip["depends_on"]:
                report.require(indexes["clips"].get(dep, {}).get("status") == "prepared",
                               path + ".depends_on", "dependency is not prepared")
        if task != "edit":
            report.require(clip["duration_seconds"] <= limits["generation_seconds"],
                           path + ".duration_seconds", "generation exceeds duration limit")
        cursor, ordered = 0, []
        for segment in clip["timeline"]:
            report.require(segment["start"] == cursor and segment["end"] > segment["start"],
                           path + ".timeline", "timeline must start at zero and be continuous")
            cursor = segment["end"]
            if not ordered or ordered[-1] != segment["shot_id"]:
                ordered.append(segment["shot_id"])
        report.require(cursor == clip["duration_seconds"] and ordered == clip["shot_ids"],
                       path + ".timeline", "timeline must cover duration in shot_ids order")
        bound = validate_bindings(clip, assets, limits, report)
        if task == "text_to_video":
            report.require(not bound, path + ".bindings", "text task must not have bindings")
        if task == "reference_to_video":
            report.require(bool(bound), path + ".bindings", "reference task needs bindings")
        frame_fields = ("first_frame_id", "last_frame_id")
        required_frames = (frame_fields if task == "first_last_frame" else
                           frame_fields[:1] if task == "image_to_video" else ())
        for field in frame_fields:
            aid = clip[field]
            if field not in required_frames:
                report.require(aid is None, path + "." + field,
                               "dedicated frame field is not valid for this task")
                continue
            asset = assets.get(aid)
            if report.require(asset is not None and asset["media_type"] == "image",
                              path + "." + field, "dedicated frame requires an image asset"):
                report.require(aid in bound, path + ".bindings", "dedicated frame must be bound")
                match_ratio(asset, clip["aspect_ratio"], prepared, path + "." + field, report)
        if task in ("edit", "extend"):
            source = assets.get(clip["source_video_id"])
            if report.require(source is not None and source["media_type"] == "video",
                              path + ".source_video_id", "edit/extend needs a source video"):
                report.require(source["id"] in bound, path + ".bindings",
                               "source video must be bound")
                if task == "extend":
                    report.require(source["status"] == "accepted" and
                                   source["observation"] != "planned",
                                   path + ".source_video_id", "extension requires accepted source state")
                else:
                    interval = clip["edit_range"]
                    if report.require(interval is not None, path + ".edit_range",
                                      "edit needs an explicit range"):
                        report.require(interval["end"] > interval["start"], path + ".edit_range",
                                       "edit range must move forward")
                        if known(source["duration_seconds"], prepared,
                                 path + ".source_video_id.duration_seconds", report):
                            report.require(interval["end"] <= source["duration_seconds"],
                                           path + ".edit_range", "range exceeds source duration")
                    if source["duration_seconds"] is not None:
                        report.require(clip["duration_seconds"] == source["duration_seconds"],
                                       path + ".duration_seconds", "edit inherits source duration")
                    match_ratio(source, clip["aspect_ratio"], prepared, path, report)
        else:
            report.require(clip["source_video_id"] is None, path + ".source_video_id",
                           "source video field is only for edit/extend")
        if task == "edit":
            report.require(bool(clip["edit_change"]) and bool(clip["preserve"]),
                           path + ".edit_change", "edit needs change and preserve instructions")
        else:
            report.require(clip["edit_range"] is None and clip["edit_change"] is None,
                           path + ".edit_range", "edit fields must be null outside edit")
        if task == "extend":
            if known(clip["extension_depth"], prepared, path + ".extension_depth", report):
                report.require(clip["extension_depth"] <= profile["extension"]["documented_depth"],
                               path + ".extension_depth", "exceeds documented extension depth")
            if clip["source_clip_id"] is not None:
                ref(clip["source_clip_id"], indexes["clips"], path + ".source_clip_id", report)
                report.require(clip["source_clip_id"] in clip["depends_on"],
                               path + ".depends_on", "source clip must be a dependency")
        else:
            report.require(clip["extension_depth"] is None and clip["source_clip_id"] is None,
                           path + ".extension_depth", "extension fields must be null outside extend")
        if project["aspect_ratio"]:
            report.require(ratio(clip["aspect_ratio"]) == ratio(project["aspect_ratio"]),
                           path + ".aspect_ratio", "task and project ratio must agree")
    acyclic({clip["id"]: clip["depends_on"] for clip in data["clips"]},
            "$.clips.depends_on", report)
    if any(clip["task"] in ("edit", "extend") for clip in data["clips"]):
        report.warn("$.project.total_seconds", "manually check edited/extended assembly without double counting")
    elif data["clips"] and project["total_seconds"] is not None:
        report.require(sum(c["duration_seconds"] for c in data["clips"]) == project["total_seconds"],
                       "$.project.total_seconds", "new-generation task durations do not match total")


def validate_skill(root, report):
    for path in root.rglob("*"):
        if not report.require(path.resolve().is_relative_to(root), str(path),
                              "file or directory symlink escapes skill root"):
            return
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\nname: ([^\n]+)\ndescription: ([^\n]+)\n---\n(.+)", text, re.S)
    if report.require(match is not None, "SKILL.md", "expected plain name/description frontmatter"):
        name, description, body = match.groups()
        report.require(name == root.name and
                       bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)) and
                       2 <= len(name) <= 64, "SKILL.md.name", "name must match directory")
        report.require(bool(description.strip()) and description[0] not in "'\"" and
                       not any(x in description for x in (": ", "<", ">", "TODO")),
                       "SKILL.md.description", "invalid unquoted description")
        report.require(bool(body.strip()), "SKILL.md.body", "body is empty")
    report.require(len(text.splitlines()) < 500, "SKILL.md", "entry must stay below 500 lines")
    for path in root.rglob("*.md"):
        report.require(path.resolve().is_relative_to(root), str(path), "external document symlink")
        if not path.resolve().is_relative_to(root):
            continue
        content = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
            parsed = urlsplit(target)
            if parsed.scheme in ("http", "https"):
                continue
            try:
                dest = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                if parsed.scheme or not dest.is_relative_to(root):
                    raise ValueError("internal link escapes skill")
                report.require(dest.is_file(), str(path), f"missing link {target}")
                if parsed.fragment and dest.is_file():
                    headings = re.findall(r"^#{1,6}\s+(.+)$", dest.read_text(), re.M)
                    anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-")
                               for h in headings}
                    report.require(unquote(parsed.fragment) in anchors, str(path),
                                   f"missing anchor {target}")
            except (ValueError, OSError, RuntimeError) as exc:
                report.require(False, str(path), str(exc))
    library = load_library(root, report)
    validate_prompt_presets(root, report)
    template = load_json(root / "assets/style-card.template.json")
    if shape(template, PRESET, "style-card.template.json", report):
        validate_preset(template, library, "style-card.template.json", report)
    paths = [root / "assets/production-package.template.json"]
    paths += [root / "assets/examples" / f"{name}-package.json"
              for name in ("narrative", "product", "animation")]
    for path in paths:
        validate_package(load_json(path), path.parent, library, report,
                         load_json(root / "assets/seedance-25-profile.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("skill", "package"))
    parser.add_argument("path")
    args = parser.parse_args()
    report = Report()
    try:
        path = Path(args.path).resolve()
        if args.mode == "skill":
            validate_skill(path, report)
        else:
            data = load_json(path)
            library = load_library(ROOT, report)
            validate_package(data, path.parent, library, report)
    except (OSError, UnicodeError) as exc:
        print(f"READ ERROR {args.path}: {exc}; fix: provide a readable UTF-8 path")
        return 2
    except (ValueError, RecursionError) as exc:
        report.require(False, args.path, str(exc), "provide valid finite UTF-8 JSON")
    print(f"RESULT errors={report.errors} warnings={report.warnings}; no media was generated")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
