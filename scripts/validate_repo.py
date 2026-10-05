"""Check lesson pairing, image links, manifests, and forbidden media."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "course"
LESSON_RE = re.compile(r"^(L\d{2}-\d{2})-.+\.md$")
PROMPT_RE = re.compile(r"^(L\d{2}-\d{2})-.+-提示词\.md$")
IMAGE_RE = re.compile(
    r"!\[[^\]]*\]\(([^)]+)\)|<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".m4v", ".mkv"}
UNPROMPTED = {
    "01-景别/教学/图/L01-01-景别阶梯总览.jpg",
    "assets/social-preview.jpg",
}
EXPECTED_LESSONS = 71


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def children(path: Path, cache: dict[Path, dict[str, Path]]) -> dict[str, Path]:
    listed = cache.get(path)
    if listed is None:
        listed = {item.name: item for item in path.iterdir()} if path.is_dir() else {}
        cache[path] = listed
    return listed


def resolve_exact(start: Path, relative: str, cache: dict[Path, dict[str, Path]]) -> Path | None:
    current = start
    for part in Path(relative).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            current = current.parent
            continue
        match = children(current, cache).get(part)
        if match is None:
            return None
        current = match
    return current if current.is_file() else None


def image_target(raw: str) -> str | None:
    text = raw.strip()
    if not text or text.startswith("#"):
        return None
    if text.startswith("<"):
        end = text.find(">")
        text = text[1:end] if end != -1 else text[1:]
    else:
        text = text.split()[0]
    text = text.split("#", 1)[0].split("?", 1)[0]
    if not text or "://" in text or text.startswith("//"):
        return None
    suffix = Path(text).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        return None
    return text


def iter_markdown(root: Path):
    for path in root.rglob("*.md"):
        if any(part in {".git", "__pycache__"} for part in path.parts):
            continue
        yield path


def check_lessons(report: Report) -> None:
    lessons: dict[str, Path] = {}
    prompts: dict[str, Path] = {}
    for path in COURSE.rglob("*.md"):
        relative = path.relative_to(COURSE).as_posix()
        if "/教学/" in relative and LESSON_RE.match(path.name):
            lessons[LESSON_RE.match(path.name).group(1)] = path
        elif "/提示词/" in relative and PROMPT_RE.match(path.name):
            prompts[PROMPT_RE.match(path.name).group(1)] = path
    if len(lessons) != EXPECTED_LESSONS or len(prompts) != EXPECTED_LESSONS:
        report.fail(f"expected {EXPECTED_LESSONS} lessons and prompts, found {len(lessons)} and {len(prompts)}")
    missing_prompts = sorted(set(lessons) - set(prompts))
    missing_lessons = sorted(set(prompts) - set(lessons))
    if missing_prompts:
        report.fail("lessons without prompts: " + ", ".join(missing_prompts))
    if missing_lessons:
        report.fail("prompts without lessons: " + ", ".join(missing_lessons))
    for lesson_id, lesson_path in lessons.items():
        prompt_path = prompts.get(lesson_id)
        if prompt_path and lesson_path.parents[1] != prompt_path.parents[1]:
            report.fail(f"{lesson_id} lesson and prompt are in different modules")


def check_image_links(report: Report) -> None:
    cache: dict[Path, dict[str, Path]] = {}
    for path in iter_markdown(ROOT):
        text = path.read_text(encoding="utf-8")
        for match in IMAGE_RE.finditer(text):
            raw = match.group(1) if match.group(1) is not None else match.group(2)
            target = image_target(raw)
            if target is None:
                continue
            if target.startswith("/"):
                report.fail(f"{path.relative_to(ROOT)}: site path is not a repo file: {target}")
                continue
            if resolve_exact(path.parent, target, cache) is None:
                report.fail(f"{path.relative_to(ROOT)}: missing image {target}")


def course_images() -> list[str]:
    found = []
    for path in COURSE.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            found.append(path.relative_to(COURSE).as_posix())
    return found


def check_manifests(report: Report) -> None:
    manifest_path = COURSE / "meta" / "images-manifest.json"
    frames_path = COURSE / "meta" / "official-frames.json"
    manifest = load_json(manifest_path)
    frames = load_json(frames_path)
    if not isinstance(manifest, list):
        report.fail("images-manifest.json must be a list")
        return
    rels = []
    for index, item in enumerate(manifest):
        if not isinstance(item, dict):
            report.fail(f"images-manifest[{index}] must be an object")
            continue
        rel = item.get("rel")
        if not isinstance(rel, str) or not rel:
            report.fail(f"images-manifest[{index}] missing rel")
            continue
        rels.append(rel)
        for field in ("caption", "prompt", "ratio"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                report.fail(f"{rel}: missing {field}")
        if not (COURSE / rel).is_file():
            report.fail(f"manifest rel missing on disk: {rel}")
    if len(rels) != len(set(rels)):
        report.fail("images-manifest.json has duplicate rel values")

    images = set(course_images())
    official_files = {rel for rel in images if Path(rel).name.startswith("seedance25-")}
    misplaced = sorted(rel for rel in official_files if not rel.startswith("附录/图/"))
    if misplaced:
        report.fail("official frames outside 附录/图: " + ", ".join(misplaced))

    included = []
    for item in frames.get("items", []):
        status = item.get("status")
        rel = item.get("rel")
        if status == "included":
            if not isinstance(rel, str):
                report.fail(f"included official item {item.get('id')} has no rel")
            else:
                included.append(rel)
                if not (COURSE / rel).is_file():
                    report.fail(f"official rel missing on disk: {rel}")
        elif status == "link_only":
            if rel is not None:
                report.fail(f"link_only official item {item.get('id')} should not have a local file")
        else:
            report.fail(f"unknown official status for {item.get('id')}: {status}")
    if set(included) != official_files:
        report.fail(
            "official frame files and included records differ: "
            + ", ".join(sorted(set(included).symmetric_difference(official_files)))
        )

    prompted = images - official_files - UNPROMPTED
    manifest_set = set(rels)
    missing = sorted(prompted - manifest_set)
    extra = sorted(manifest_set - prompted)
    if missing:
        report.fail("images missing from images-manifest.json: " + ", ".join(missing[:20]))
    if extra:
        report.fail("manifest entries without a course image: " + ", ".join(extra[:20]))
    for rel in sorted(UNPROMPTED):
        if rel not in images:
            report.fail(f"expected unprompted image missing: {rel}")
        if rel in manifest_set:
            report.fail(f"unprompted image should stay out of the manifest: {rel}")


def check_forbidden(report: Report) -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "__pycache__"} for part in path.parts):
            continue
        suffix = path.suffix.lower()
        if suffix in VIDEO_SUFFIXES or suffix == ".webp":
            report.fail(f"forbidden file: {path.relative_to(ROOT)}")


def main() -> int:
    report = Report()
    check_lessons(report)
    check_image_links(report)
    check_manifests(report)
    check_forbidden(report)
    if report.errors:
        print(f"{len(report.errors)} error(s)")
        for message in report.errors[:80]:
            print(message)
        if len(report.errors) > 80:
            print(f"... {len(report.errors) - 80} more")
        return 1
    print("ok: 71 lessons, manifests, image links, no video or webp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
