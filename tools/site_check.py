#!/usr/bin/env python
"""No-network static-site checks for perth.bitdevs.com.au."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
LOCAL_ATTRS = ("href", "src")
SKIP_SCHEMES = {
    "data",
    "http",
    "https",
    "javascript",
    "mailto",
    "sms",
    "tel",
}
SKIP_DIRS = {
    ".beads",
    ".dolt",
    ".git",
    ".playwright-mcp",
    ".venv",
    "_docs",
    "env",
    "node_modules",
    "venv",
}
SEVERITY_ORDER = {"error": 0, "warning": 1}


@dataclass(frozen=True)
class Tag:
    name: str
    attrs: dict[str, str]
    line: int


@dataclass(frozen=True)
class HtmlPage:
    path: Path
    rel_path: str
    text: str
    tags: list[Tag]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int
    message: str


class TagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[Tag] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        self.tags.append(Tag(tag.lower(), attr_map, self.getpos()[0]))


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_skipped(path: Path, root: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.relative_to(root).parts)


def read_html(path: Path, root: Path) -> HtmlPage:
    text = path.read_text(encoding="utf-8", errors="ignore")
    parser = TagCollector()
    parser.feed(text)
    return HtmlPage(path=path, rel_path=rel(path, root), text=text, tags=parser.tags)


def html_pages(root: Path) -> list[HtmlPage]:
    pages: list[HtmlPage] = []
    for path in sorted(root.rglob("*.html")):
        if is_skipped(path, root):
            continue
        pages.append(read_html(path, root))
    return pages


def add(finding_list: list[Finding], severity: str, code: str, path: str, line: int, message: str) -> None:
    finding_list.append(Finding(severity, code, path, line, message))


def local_target(root: Path, page: HtmlPage, value: str) -> Path | None:
    value = html.unescape(value.strip())
    if not value or value.startswith(("#", "?")):
        return None

    parsed = urlsplit(value)
    if parsed.scheme.lower() in SKIP_SCHEMES or parsed.netloc:
        return None
    if not parsed.path:
        return None

    target_path = unquote(parsed.path)
    if target_path.startswith("/"):
        target = root / target_path.lstrip("/")
    else:
        target = page.path.parent / target_path

    if target_path.endswith("/"):
        return target / "index.html"
    if target.exists() and target.is_dir():
        return target / "index.html"
    if not target.suffix and (target / "index.html").exists():
        return target / "index.html"
    return target


def check_local_targets(root: Path, pages: list[HtmlPage], findings: list[Finding]) -> None:
    root_resolved = root.resolve()
    for page in pages:
        for tag in page.tags:
            for attr_name in LOCAL_ATTRS:
                value = tag.attrs.get(attr_name)
                if value is None:
                    continue
                target = local_target(root, page, value)
                if target is None:
                    continue
                try:
                    target.resolve().relative_to(root_resolved)
                except ValueError:
                    add(
                        findings,
                        "error",
                        "local-target-outside-root",
                        page.rel_path,
                        tag.line,
                        f"{attr_name} points outside the site root: {value}",
                    )
                    continue
                if not target.exists():
                    add(
                        findings,
                        "error",
                        "broken-local-target",
                        page.rel_path,
                        tag.line,
                        f"{attr_name} target does not exist: {value}",
                    )


def check_target_blank_rel(pages: list[HtmlPage], findings: list[Finding]) -> None:
    for page in pages:
        for tag in page.tags:
            if tag.name != "a":
                continue
            if tag.attrs.get("target", "").lower() != "_blank":
                continue
            rel_tokens = set(tag.attrs.get("rel", "").lower().split())
            if "noopener" in rel_tokens:
                continue
            href = tag.attrs.get("href", "")
            add(
                findings,
                "error",
                "blank-target-without-noopener",
                page.rel_path,
                tag.line,
                f'target="_blank" link missing rel="noopener": {href}',
            )


def month_for_page(page: HtmlPage) -> str | None:
    parent = page.path.parent.name
    if MONTH_RE.fullmatch(parent):
        return parent
    return None


def is_slide_topic_page(page: HtmlPage) -> bool:
    month = month_for_page(page)
    return month is not None and month >= "2026-02" and page.path.name != "index.html"


def body_css(text: str) -> str:
    blocks = re.findall(r"body\s*\{([^}]*)\}", text, flags=re.IGNORECASE | re.DOTALL)
    return ";".join(blocks)


def strict_slide_months(root: Path) -> set[str]:
    months: set[str] = set()
    for month_dir in month_dirs_with_manifests(root):
        months.add(month_dir.name)
    return months


def check_slide_conventions(pages: list[HtmlPage], findings: list[Finding], strict_months: set[str]) -> None:
    for page in pages:
        if not is_slide_topic_page(page):
            continue
        month = month_for_page(page)
        assert month is not None
        month_href = f"/{month}/"
        compact_body = re.sub(r"\s+", "", body_css(page.text).lower())
        severity = "error" if month in strict_months else "warning"

        if "overflow-x:hidden" not in compact_body:
            add(
                findings,
                severity,
                "slide-missing-overflow-x-hidden",
                page.rel_path,
                1,
                "slide topic body must include overflow-x:hidden",
            )
        if re.search(r"(^|;)overflow:hidden($|;)", compact_body):
            add(
                findings,
                severity,
                "slide-body-overflow-hidden",
                page.rel_path,
                1,
                "slide topic body must not use overflow:hidden",
            )
        # Escape-back is provided either by an inline keydown handler OR by
        # linking the shared /assets/slides.js (which derives the month URL
        # from location.pathname).
        has_inline_escape = "Escape" in page.text and month_href in page.text
        has_shared_runtime = "/assets/slides.js" in page.text
        if not (has_inline_escape or has_shared_runtime):
            add(
                findings,
                severity,
                "slide-missing-escape-back",
                page.rel_path,
                1,
                f"slide topic must handle Escape back to {month_href}",
            )
        if "Topics" not in page.text or month_href not in page.text:
            add(
                findings,
                severity,
                "slide-missing-topics-link",
                page.rel_path,
                1,
                f"slide topic must include a visible Topics link to {month_href}",
            )


def load_manifest(path: Path, root: Path, findings: list[Finding]) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add(findings, "error", "manifest-json", rel(path, root), exc.lineno, exc.msg)
        return None
    if not isinstance(data, dict):
        add(findings, "error", "manifest-shape", rel(path, root), 1, "manifest must be a JSON object")
        return None
    return data


def require_keys(
    data: dict[str, object],
    keys: list[str],
    findings: list[Finding],
    path: str,
    context: str,
) -> None:
    for key in keys:
        if key not in data:
            add(findings, "error", "manifest-missing-key", path, 1, f"{context} missing key: {key}")


def manifest_page_file(item: object) -> str | None:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("file"), str):
        return str(item["file"])
    return None


def manifest_parent_topic(item: object) -> str | None:
    if isinstance(item, dict) and isinstance(item.get("parent_topic"), str):
        return str(item["parent_topic"])
    return None


def href_to_file_pattern(file_name: str) -> re.Pattern[str]:
    escaped = re.escape(file_name)
    return re.compile(r"""href\s*=\s*["']""" + escaped + r"""(?:[?#][^"']*)?["']""")


def check_manifest(root: Path, month_dir: Path, findings: list[Finding]) -> dict[str, object] | None:
    manifest_path = month_dir / "manifest.json"
    data = load_manifest(manifest_path, root, findings)
    manifest_rel = rel(manifest_path, root)
    if data is None:
        return None

    require_keys(
        data,
        ["schema_version", "month", "status", "event", "topics", "auxiliary_pages"],
        findings,
        manifest_rel,
        "manifest",
    )

    month = data.get("month")
    if month != month_dir.name:
        add(
            findings,
            "error",
            "manifest-month-mismatch",
            manifest_rel,
            1,
            f"manifest month {month!r} does not match directory {month_dir.name}",
        )

    event = data.get("event")
    if isinstance(event, dict):
        require_keys(
            event,
            ["title", "date", "date_label", "time_label", "timezone", "venue"],
            findings,
            manifest_rel,
            "event",
        )
    else:
        add(findings, "error", "manifest-event-shape", manifest_rel, 1, "event must be an object")

    topics = data.get("topics")
    if not isinstance(topics, list):
        add(findings, "error", "manifest-topics-shape", manifest_rel, 1, "topics must be a list")
        topics = []

    auxiliary_pages = data.get("auxiliary_pages")
    if not isinstance(auxiliary_pages, list):
        add(
            findings,
            "error",
            "manifest-auxiliary-shape",
            manifest_rel,
            1,
            "auxiliary_pages must be a list",
        )
        auxiliary_pages = []

    topic_count = data.get("topic_count")
    if topic_count is not None and topic_count != len(topics):
        add(
            findings,
            "error",
            "manifest-topic-count",
            manifest_rel,
            1,
            f"topic_count is {topic_count}, but topics has {len(topics)} entries",
        )

    hub_path = month_dir / "index.html"
    hub_text = hub_path.read_text(encoding="utf-8", errors="ignore") if hub_path.exists() else ""
    if not hub_path.exists():
        add(findings, "error", "manifest-missing-hub", manifest_rel, 1, "month hub index.html is missing")

    declared_topics: set[str] = set()
    for index, topic in enumerate(topics, start=1):
        if not isinstance(topic, dict):
            add(findings, "error", "manifest-topic-shape", manifest_rel, 1, f"topic #{index} must be an object")
            continue
        require_keys(topic, ["file", "title", "category", "status", "summary"], findings, manifest_rel, f"topic #{index}")
        file_name = manifest_page_file(topic)
        if file_name is None:
            continue
        declared_topics.add(file_name)
        if "/" in file_name or file_name == "index.html":
            add(findings, "error", "manifest-topic-file", manifest_rel, 1, f"invalid topic file: {file_name}")
            continue
        if not (month_dir / file_name).exists():
            add(findings, "error", "manifest-topic-missing-file", manifest_rel, 1, f"topic file is missing: {file_name}")
        if hub_text and not href_to_file_pattern(file_name).search(hub_text):
            add(findings, "error", "manifest-topic-not-linked", rel(hub_path, root), 1, f"hub does not link topic file: {file_name}")

    declared_auxiliary: set[str] = set()
    for index, item in enumerate(auxiliary_pages, start=1):
        if not isinstance(item, dict):
            add(
                findings,
                "error",
                "manifest-auxiliary-shape",
                manifest_rel,
                1,
                f"auxiliary page #{index} must be an object with file, title, parent_topic, status, and summary",
            )
            continue
        require_keys(
            item,
            ["file", "title", "parent_topic", "status", "summary"],
            findings,
            manifest_rel,
            f"auxiliary page #{index}",
        )
        file_name = manifest_page_file(item)
        if file_name is None:
            add(
                findings,
                "error",
                "manifest-auxiliary-shape",
                manifest_rel,
                1,
                f"auxiliary page #{index} file must be a string",
            )
            continue
        parent_topic = manifest_parent_topic(item)
        if "parent_topic" in item and parent_topic is None:
            add(
                findings,
                "error",
                "manifest-auxiliary-shape",
                manifest_rel,
                1,
                f"auxiliary page #{index} parent_topic must be a topic file",
            )
        elif parent_topic is not None and parent_topic not in declared_topics:
            add(
                findings,
                "error",
                "manifest-auxiliary-parent",
                manifest_rel,
                1,
                f"auxiliary page {file_name} parent_topic is not listed in topics: {parent_topic}",
            )
        declared_auxiliary.add(file_name)
        if "/" in file_name or file_name == "index.html":
            add(
                findings,
                "error",
                "manifest-auxiliary-file",
                manifest_rel,
                1,
                f"invalid auxiliary page file: {file_name}",
            )
            continue
        if file_name in declared_topics:
            add(
                findings,
                "error",
                "manifest-auxiliary-duplicate",
                manifest_rel,
                1,
                f"auxiliary page is also listed as a topic: {file_name}",
            )
        if not (month_dir / file_name).exists():
            add(
                findings,
                "error",
                "manifest-auxiliary-missing-file",
                manifest_rel,
                1,
                f"auxiliary page file is missing: {file_name}",
            )

    actual_pages = {path.name for path in month_dir.glob("*.html") if path.name != "index.html"}
    declared_pages = declared_topics | declared_auxiliary
    for file_name in sorted(actual_pages - declared_pages):
        add(
            findings,
            "error",
            "month-page-unclassified",
            rel(month_dir / file_name, root),
            1,
            "month HTML page is not listed in manifest topics or auxiliary_pages",
        )

    if isinstance(event, dict) and hub_text:
        for key in ("date_label", "time_label"):
            value = event.get(key)
            if isinstance(value, str) and value not in hub_text:
                add(
                    findings,
                    "error",
                    "manifest-hub-mismatch",
                    rel(hub_path, root),
                    1,
                    f"hub does not contain event {key}: {value}",
                )
        venue = event.get("venue")
        if isinstance(venue, dict):
            venue_label = venue.get("label")
            if isinstance(venue_label, str) and venue_label not in hub_text:
                add(
                    findings,
                    "error",
                    "manifest-hub-mismatch",
                    rel(hub_path, root),
                    1,
                    f"hub does not contain venue label: {venue_label}",
                )

    return data


def month_dirs_with_manifests(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and MONTH_RE.fullmatch(path.name) and (path / "manifest.json").exists()
    )


def check_manifests(root: Path, findings: list[Finding]) -> None:
    manifests: list[tuple[Path, dict[str, object]]] = []
    for month_dir in month_dirs_with_manifests(root):
        data = check_manifest(root, month_dir, findings)
        if data is not None:
            manifests.append((month_dir, data))

    upcoming = [(month_dir, data) for month_dir, data in manifests if data.get("status") == "upcoming"]
    if len(upcoming) > 1:
        months = ", ".join(month_dir.name for month_dir, _ in upcoming)
        add(findings, "error", "multiple-upcoming-manifests", "index.html", 1, f"multiple manifests marked upcoming: {months}")
    if len(upcoming) != 1:
        return

    month_dir, data = upcoming[0]
    root_index = root / "index.html"
    root_text = root_index.read_text(encoding="utf-8", errors="ignore") if root_index.exists() else ""
    manifest_rel = rel(month_dir / "manifest.json", root)
    event = data.get("event")
    landing = data.get("landing")
    href = f"/{month_dir.name}/"
    if isinstance(landing, dict) and isinstance(landing.get("href"), str):
        href = str(landing["href"])

    if not root_text:
        add(findings, "error", "missing-root-index", manifest_rel, 1, "root index.html is missing")
        return
    if href not in root_text:
        add(findings, "error", "manifest-landing-mismatch", "index.html", 1, f"landing page does not link upcoming month href: {href}")
    if isinstance(event, dict):
        for key in ("date_label", "time_label"):
            value = event.get(key)
            if isinstance(value, str) and value not in root_text:
                add(
                    findings,
                    "error",
                    "manifest-landing-mismatch",
                    "index.html",
                    1,
                    f"landing page does not contain event {key}: {value}",
                )
        venue = event.get("venue")
        if isinstance(venue, dict):
            venue_label = venue.get("label")
            if isinstance(venue_label, str) and venue_label not in root_text:
                add(
                    findings,
                    "error",
                    "manifest-landing-mismatch",
                    "index.html",
                    1,
                    f"landing page does not contain venue label: {venue_label}",
                )


def summarize(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        key = f"{finding.severity}:{finding.code}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def print_findings(findings: list[Finding], *, max_findings: int) -> None:
    ordered = sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], item.path, item.line, item.code))
    shown = ordered if max_findings <= 0 else ordered[:max_findings]
    for finding in shown:
        location = f"{finding.path}:{finding.line}" if finding.line else finding.path
        print(f"{finding.severity.upper()} {finding.code} {location} - {finding.message}")
    if len(shown) < len(ordered):
        print(f"... {len(ordered) - len(shown)} more findings omitted; rerun with --max-findings 0 to show all.")

    if findings:
        print()
        print("Finding summary:")
        for key, count in sorted(summarize(findings).items()):
            print(f"  {key}: {count}")


def run(root: Path, *, strict: bool, max_findings: int) -> int:
    findings: list[Finding] = []
    pages = html_pages(root)

    check_local_targets(root, pages, findings)
    check_slide_conventions(pages, findings, strict_slide_months(root))
    check_manifests(root, findings)
    check_target_blank_rel(pages, findings)

    print_findings(findings, max_findings=max_findings)

    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warning")
    manifest_count = len(month_dirs_with_manifests(root))
    print(f"Checked {len(pages)} HTML files and {manifest_count} manifest file(s).")
    print(f"Errors: {errors}. Warnings: {warnings}.")
    if warnings and not strict:
        print("Warnings do not fail site-check unless --strict is used.")
    if errors or (strict and warnings):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="Site root to check")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--max-findings", type=int, default=120, help="Maximum findings to print, or 0 for all")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(Path(args.root).resolve(), strict=args.strict, max_findings=args.max_findings)


if __name__ == "__main__":
    raise SystemExit(main())
