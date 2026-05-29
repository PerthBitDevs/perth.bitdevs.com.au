#!/usr/bin/env python
"""Collect curated Bitcoin source changes for Perth BitDevs planning."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import os
import re
import sys
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


ROOT = Path(__file__).resolve().parents[2]
NEWSWATCH_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCES_PATH = NEWSWATCH_DIR / "sources.json"
DEFAULT_STATE_PATH = NEWSWATCH_DIR / "state.local.json"
DEFAULT_RUNS_DIR = NEWSWATCH_DIR / "runs"
DEFAULT_GITHUB_REPO = "PerthBitDevs/PerthBitDevs"
GITHUB_API_URL = "https://api.github.com"
USER_AGENT = "PerthBitDevsNewswatch/1.0 (+https://perth.bitdevs.com.au)"
MAX_SEEN_IDS = 500

VALID_KINDS = {"feed", "page"}
VALID_PRIORITIES = {"high", "medium", "low"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
}
STOPWORDS = {
    "about",
    "after",
    "against",
    "bitcoin",
    "bitcoins",
    "from",
    "have",
    "into",
    "latest",
    "more",
    "news",
    "over",
    "that",
    "their",
    "this",
    "with",
    "without",
}
URL_RE = re.compile(r"https?://[^\"'<>\s)]+")


@dataclass
class Source:
    id: str
    title: str
    category: str
    kind: str
    url: str
    priority: str
    tags: list[str]
    enabled: bool = True


@dataclass
class Candidate:
    source_id: str
    source_title: str
    category: str
    priority: str
    tags: list[str]
    kind: str
    title: str
    url: str
    canonical_url: str
    raw_id: str
    published_at: str | None
    summary: str
    excerpt: str
    already_cited_paths: list[str] = field(default_factory=list)
    possible_repeat_paths: list[str] = field(default_factory=list)
    duplicate_sources: list[str] = field(default_factory=list)


@dataclass
class SourceFailure:
    source_id: str
    source_title: str
    url: str
    error: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def isoformat(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, tuple) and len(value) >= 6:
        dt = datetime(*value[:6], tzinfo=timezone.utc)
    else:
        try:
            dt = date_parser.parse(str(value))
        except (TypeError, ValueError, OverflowError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clean_text(value: str, *, max_chars: int | None = None) -> str:
    if re.search(r"<[a-zA-Z!/][^>]*>", value or ""):
        text = BeautifulSoup(value or "", "html.parser").get_text(" ")
    else:
        text = value or ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_chars is not None and len(text) > max_chars:
        return text[: max_chars - 1].rstrip() + "..."
    return text


def raw_urls(text: str) -> list[str]:
    return [url.rstrip(".,;") for url in URL_RE.findall(text)]


def canonicalize_url(url: str) -> str:
    parsed = urlparse(html.unescape(url.strip()))
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS and not key.lower().startswith("utm_")
    ]
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def parse_github_issue_ref(value: str, default_repo: str) -> tuple[str, int]:
    """Parse issue refs like 36, owner/repo#36, or a GitHub issue URL."""
    value = value.strip()
    if not value:
        raise ValueError("empty GitHub issue reference")

    default_repo = default_repo.strip("/")
    if "/" not in default_repo:
        raise ValueError("--github-repo must be in owner/repo form")

    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 4 and parts[2] == "issues":
            return f"{parts[0]}/{parts[1]}", int(parts[3])
        raise ValueError(f"unsupported GitHub issue URL: {value}")

    if "#" in value:
        repo, number = value.rsplit("#", 1)
        repo = repo.strip("/")
        if "/" not in repo:
            repo = default_repo
        return repo, int(number)

    if re.fullmatch(r"\d+", value):
        return default_repo, int(value)

    match = re.fullmatch(r"([^/]+)/([^/]+)/issues/(\d+)", value)
    if match:
        return f"{match.group(1)}/{match.group(2)}", int(match.group(3))

    raise ValueError(f"unsupported GitHub issue reference: {value}")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_sources(path: Path) -> list[Source]:
    data = load_json(path, [])
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")

    sources: list[Source] = []
    seen_ids: set[str] = set()
    required = {"id", "title", "category", "kind", "url", "priority", "tags", "enabled"}
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"source #{index + 1} must be an object")
        missing = sorted(required - item.keys())
        if missing:
            raise ValueError(f"source #{index + 1} missing fields: {', '.join(missing)}")
        if item["id"] in seen_ids:
            raise ValueError(f"duplicate source id: {item['id']}")
        if item["kind"] not in VALID_KINDS:
            raise ValueError(f"{item['id']}: kind must be one of {sorted(VALID_KINDS)}")
        if item["priority"] not in VALID_PRIORITIES:
            raise ValueError(f"{item['id']}: priority must be one of {sorted(VALID_PRIORITIES)}")
        if not isinstance(item["tags"], list) or not all(isinstance(tag, str) for tag in item["tags"]):
            raise ValueError(f"{item['id']}: tags must be a list of strings")
        seen_ids.add(item["id"])
        sources.append(
            Source(
                id=item["id"],
                title=item["title"],
                category=item["category"],
                kind=item["kind"],
                url=item["url"],
                priority=item["priority"],
                tags=item["tags"],
                enabled=bool(item["enabled"]),
            )
        )
    return sources


def load_state(path: Path) -> dict[str, Any]:
    state = load_json(path, {"version": 1, "last_success_at": None, "sources": {}})
    state.setdefault("version", 1)
    state.setdefault("last_success_at", None)
    state.setdefault("sources", {})
    return state


def fetch_source(
    client: httpx.Client,
    source: Source,
    source_state: dict[str, Any],
    *,
    use_validators: bool,
) -> httpx.Response | None:
    headers = {"User-Agent": USER_AGENT}
    if use_validators:
        etag = source_state.get("etag")
        last_modified = source_state.get("last_modified")
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

    response = client.get(source.url, headers=headers)
    if use_validators and response.status_code in {400, 403, 412}:
        response = client.get(source.url, headers={"User-Agent": USER_AGENT})
    if response.status_code == 304:
        return None
    response.raise_for_status()
    return response


def entry_datetime(entry: dict[str, Any]) -> datetime | None:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        dt = parse_date(entry.get(key))
        if dt is not None:
            return dt
    for key in ("published", "updated", "created"):
        dt = parse_date(entry.get(key))
        if dt is not None:
            return dt
    return None


def entry_raw_id(entry: dict[str, Any], title: str, link: str) -> str:
    raw = entry.get("id") or entry.get("guid") or link or title
    return hashlib.sha256(str(raw).encode("utf-8")).hexdigest()


def candidate_from_entry(source: Source, entry: dict[str, Any]) -> Candidate | None:
    link = entry.get("link") or ""
    title = clean_text(entry.get("title") or link or "Untitled")
    if not link and not title:
        return None
    summary = clean_text(entry.get("summary") or entry.get("description") or "", max_chars=600)
    published_dt = entry_datetime(entry)
    raw_id = entry_raw_id(entry, title, link)
    canonical = canonicalize_url(link or source.url)
    return Candidate(
        source_id=source.id,
        source_title=source.title,
        category=source.category,
        priority=source.priority,
        tags=source.tags,
        kind=source.kind,
        title=title,
        url=link or source.url,
        canonical_url=canonical,
        raw_id=raw_id,
        published_at=isoformat(published_dt),
        summary=summary,
        excerpt=summary,
    )


def parse_feed_candidates(
    source: Source,
    content: bytes,
    *,
    since: datetime | None,
    seen_ids: set[str],
    ignore_seen: bool,
    limit: int,
) -> tuple[list[Candidate], list[str]]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="feedparser")
        parsed = feedparser.parse(content)
    candidates: list[Candidate] = []
    observed_ids: list[str] = []

    for entry in parsed.entries:
        candidate = candidate_from_entry(source, entry)
        if candidate is None:
            continue
        observed_ids.append(candidate.raw_id)
        published_dt = parse_date(candidate.published_at)
        if not ignore_seen and candidate.raw_id in seen_ids:
            continue
        if since is not None and published_dt is not None and published_dt <= since:
            continue
        candidates.append(candidate)
        if len(candidates) >= limit:
            break

    return candidates, observed_ids


def extract_page_candidate(source: Source, content: str) -> tuple[Candidate, str]:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = clean_text(soup.title.string if soup.title else source.title) or source.title
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = ""
    if description_tag and description_tag.get("content"):
        description = clean_text(description_tag["content"], max_chars=500)
    page_text = clean_text(str(soup), max_chars=900)
    excerpt = description or page_text
    normalized = clean_text(str(soup))
    content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    raw_id = hashlib.sha256(f"{source.id}:{content_hash}".encode("utf-8")).hexdigest()
    return (
        Candidate(
            source_id=source.id,
            source_title=source.title,
            category=source.category,
            priority=source.priority,
            tags=source.tags,
            kind=source.kind,
            title=title,
            url=source.url,
            canonical_url=canonicalize_url(source.url),
            raw_id=raw_id,
            published_at=None,
            summary=excerpt,
            excerpt=excerpt,
        ),
        content_hash,
    )


def dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
    ordered = sorted(candidates, key=lambda item: (PRIORITY_ORDER[item.priority], item.published_at or ""))
    by_url: dict[str, Candidate] = {}
    deduped: list[Candidate] = []

    for candidate in ordered:
        existing = by_url.get(candidate.canonical_url)
        if existing is not None:
            if candidate.source_title != existing.source_title and candidate.source_title not in existing.duplicate_sources:
                existing.duplicate_sources.append(candidate.source_title)
            continue

        title_key = normalize_title(candidate.title)
        similar = next(
            (
                item
                for item in deduped
                if difflib.SequenceMatcher(None, title_key, normalize_title(item.title)).ratio() >= 0.92
            ),
            None,
        )
        if similar is not None:
            if candidate.source_title != similar.source_title and candidate.source_title not in similar.duplicate_sources:
                similar.duplicate_sources.append(candidate.source_title)
            continue

        by_url[candidate.canonical_url] = candidate
        deduped.append(candidate)

    return deduped


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def recent_month_dirs(root: Path, count: int) -> list[Path]:
    month_dirs = [
        path
        for path in root.iterdir()
        if path.is_dir() and re.fullmatch(r"\d{4}-\d{2}", path.name)
    ]
    return sorted(month_dirs, key=lambda item: item.name)[-count:]


def extract_urls(text: str) -> list[str]:
    return [canonicalize_url(url) for url in raw_urls(text)]


def topic_terms(candidate: Candidate) -> list[str]:
    words = re.findall(r"[a-z0-9]+", candidate.title.lower())
    terms = [word for word in words if len(word) >= 4 and word not in STOPWORDS]
    terms.extend(tag.lower() for tag in candidate.tags if len(tag) >= 4 and tag.lower() not in STOPWORDS)
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    return unique_terms[:8]


def scan_recent_coverage(root: Path, month_count: int) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    url_index: dict[str, list[str]] = {}
    text_index: list[tuple[str, str]] = []
    for month_dir in recent_month_dirs(root, month_count):
        for html_path in sorted(month_dir.glob("*.html")):
            rel_path = html_path.relative_to(root).as_posix()
            text = html_path.read_text(encoding="utf-8", errors="ignore")
            for url in extract_urls(text):
                url_index.setdefault(url, []).append(rel_path)
            text_index.append((rel_path, clean_text(text).lower()))
    return url_index, text_index


def mark_recent_coverage(candidates: list[Candidate], root: Path, month_count: int) -> None:
    url_index, text_index = scan_recent_coverage(root, month_count)
    for candidate in candidates:
        candidate.already_cited_paths = sorted(url_index.get(candidate.canonical_url, []))
        terms = topic_terms(candidate)
        if len(terms) < 3:
            continue
        threshold = min(3, len(terms))
        possible_paths: list[str] = []
        for rel_path, text in text_index:
            if rel_path in candidate.already_cited_paths:
                continue
            matches = sum(1 for term in terms if term in text)
            if matches >= threshold:
                possible_paths.append(rel_path)
        candidate.possible_repeat_paths = possible_paths[:5]


def merge_seen(existing: list[str], observed: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for raw_id in list(observed) + list(existing):
        if raw_id not in seen:
            seen.add(raw_id)
            merged.append(raw_id)
    return merged[:MAX_SEEN_IDS]


def scan_sources(
    sources: list[Source],
    state: dict[str, Any],
    *,
    since: datetime | None,
    explicit_since: bool,
    limit_per_source: int,
) -> tuple[list[Candidate], list[SourceFailure], dict[str, Any]]:
    candidates: list[Candidate] = []
    failures: list[SourceFailure] = []
    next_state = json.loads(json.dumps(state))
    next_state.setdefault("sources", {})

    with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(45.0)) as client:
        for source in sources:
            if not source.enabled:
                continue
            source_state = next_state["sources"].setdefault(source.id, {})
            try:
                response = fetch_source(
                    client,
                    source,
                    source_state,
                    use_validators=not explicit_since,
                )
                if response is None:
                    continue
                source_state["etag"] = response.headers.get("etag")
                source_state["last_modified"] = response.headers.get("last-modified")
                source_state["last_checked_at"] = isoformat(now_utc())

                if source.kind == "feed":
                    seen_ids = set(source_state.get("seen_ids", []))
                    source_candidates, observed_ids = parse_feed_candidates(
                        source,
                        response.content,
                        since=since,
                        seen_ids=seen_ids,
                        ignore_seen=explicit_since,
                        limit=limit_per_source,
                    )
                    candidates.extend(source_candidates)
                    source_state["seen_ids"] = merge_seen(source_state.get("seen_ids", []), observed_ids)
                elif source.kind == "page":
                    candidate, content_hash = extract_page_candidate(source, response.text)
                    changed = source_state.get("content_hash") != content_hash
                    if changed or explicit_since:
                        candidates.append(candidate)
                    source_state["content_hash"] = content_hash
                    source_state["seen_ids"] = merge_seen(source_state.get("seen_ids", []), [candidate.raw_id])
                else:
                    raise ValueError(f"unsupported source kind: {source.kind}")
            except Exception as exc:  # noqa: BLE001 - failures are reported in the packet.
                failures.append(SourceFailure(source.id, source.title, source.url, str(exc)))

    return dedupe_candidates(candidates), failures, next_state


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def markdown_heading(body: str) -> str | None:
    for line in body.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            return clean_text(match.group(1), max_chars=180)
    for line in body.splitlines():
        cleaned = clean_text(line, max_chars=180)
        if cleaned:
            return cleaned
    return None


def infer_issue_tags(title: str, body: str) -> list[str]:
    text = f"{title} {body}".lower()
    tags = ["github-issue", "community-topic"]
    keyword_tags = [
        ("silent", "silent-payments"),
        ("sparrow", "wallet"),
        ("mempool", "mempool-policy"),
        ("policy", "mempool-policy"),
        ("bitnodes", "network"),
        ("bnoc", "network"),
        ("wallet", "wallets"),
        ("claude", "ai"),
        ("ai", "ai"),
        ("vulnerability", "security"),
        ("loupe", "security"),
        ("travel rule", "regulation"),
        ("spiral", "funding"),
    ]
    for keyword, tag in keyword_tags:
        if keyword in text and tag not in tags:
            tags.append(tag)
    return tags


def candidate_from_github_issue_comment(
    repo: str,
    issue_number: int,
    comment: dict[str, Any],
    *,
    since: datetime | None,
) -> Candidate | None:
    if comment.get("isMinimized"):
        return None

    body = comment.get("body") or ""
    title = markdown_heading(body) or f"{repo} issue #{issue_number} comment"
    urls = raw_urls(body)
    comment_url = comment.get("html_url") or comment.get("url") or f"https://github.com/{repo}/issues/{issue_number}"
    primary_url = urls[0] if urls else comment_url
    created_at = parse_date(comment.get("createdAt") or comment.get("created_at"))
    updated_at = parse_date(comment.get("updatedAt") or comment.get("updated_at")) or created_at
    if since is not None and updated_at is not None and updated_at <= since:
        return None

    author = (comment.get("author") or comment.get("user") or {}).get("login") or "unknown"
    summary_parts = [clean_text(body, max_chars=600)]
    if urls:
        summary_parts.append("Submitted links: " + ", ".join(urls[:5]))
    if comment_url != primary_url:
        summary_parts.append(f"GitHub comment: {comment_url}")
    summary = " ".join(part for part in summary_parts if part)
    comment_updated_value = comment.get("updatedAt") or comment.get("updated_at") or comment.get("createdAt") or comment.get("created_at")
    raw_id = hashlib.sha256(
        f"github:{repo}:{issue_number}:{comment.get('id')}:{comment_updated_value}".encode("utf-8")
    ).hexdigest()

    return Candidate(
        source_id=f"github-issue-{issue_number}",
        source_title=f"{repo} issue #{issue_number}",
        category="community",
        priority="high",
        tags=infer_issue_tags(title, body),
        kind="github_issue",
        title=title,
        url=primary_url,
        canonical_url=canonicalize_url(primary_url) if urls else comment_url,
        raw_id=raw_id,
        published_at=isoformat(created_at),
        summary=summary,
        excerpt=f"Submitted by @{author}. {summary}",
    )


def github_issue_candidates_from_payload(
    repo: str,
    issue_number: int,
    comments: list[dict[str, Any]],
    *,
    since: datetime | None,
    limit: int,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for comment in comments:
        candidate = candidate_from_github_issue_comment(repo, issue_number, comment, since=since)
        if candidate is None:
            continue
        candidates.append(candidate)
        if len(candidates) >= limit:
            break
    return candidates


def fetch_github_issue_candidates(
    client: httpx.Client,
    repo: str,
    issue_number: int,
    *,
    since: datetime | None,
    limit: int,
) -> list[Candidate]:
    headers = github_headers()
    issue_url = f"{GITHUB_API_URL}/repos/{repo}/issues/{issue_number}"
    issue_response = client.get(issue_url, headers=headers)
    issue_response.raise_for_status()

    comments: list[dict[str, Any]] = []
    comments_url = f"{issue_url}/comments?per_page=100"
    while comments_url and len(comments) < limit:
        response = client.get(comments_url, headers=headers)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"unexpected GitHub comments payload for {repo}#{issue_number}")
        comments.extend(payload)
        comments_url = response.links.get("next", {}).get("url")

    return github_issue_candidates_from_payload(repo, issue_number, comments, since=since, limit=limit)


def packet_prompt() -> str:
    return (
        "Review these curated-source and GitHub issue candidates for the next Perth BitDevs. "
        "Classify each item as "
        "`dedicated deck`, `news roundup`, `watch`, or `ignore`. Prefer technical "
        "Bitcoin protocol, wallet, privacy, mining, Lightning, security, and open-source "
        "development items. Apply the repo content budget: 6-8 topic decks, 3-5 slides "
        "per deck, and use `news-roundup.html` for interesting items that do not justify "
        "a full deck. Give community-submitted GitHub issue topics extra editorial weight. "
        "Flag contested claims that need source verification before slides are written."
    )


def markdown_candidate(candidate: Candidate) -> str:
    lines = [
        f"### {candidate.title}",
        f"- Source: {candidate.source_title} (`{candidate.source_id}`)",
        f"- Priority: {candidate.priority}",
        f"- Category: {candidate.category}",
        f"- Tags: {', '.join(candidate.tags)}",
        f"- Published: {candidate.published_at or 'unknown'}",
        f"- Link: {candidate.url}",
    ]
    if candidate.already_cited_paths:
        lines.append(f"- Already cited: {', '.join(candidate.already_cited_paths)}")
    if candidate.possible_repeat_paths:
        lines.append(f"- Possible repeat: {', '.join(candidate.possible_repeat_paths)}")
    if candidate.duplicate_sources:
        lines.append(f"- Also seen via: {', '.join(candidate.duplicate_sources)}")
    if candidate.excerpt:
        lines.append("")
        lines.append(candidate.excerpt)
    lines.append("")
    return "\n".join(lines)


def render_markdown_packet(packet: dict[str, Any]) -> str:
    candidates = [Candidate(**item) for item in packet["candidates"]]
    failures = [SourceFailure(**item) for item in packet["failures"]]
    lines = [
        "# Bitcoin Newswatch Packet",
        "",
        f"- Generated: {packet['generated_at']}",
        f"- Window start: {packet['since'] or 'first run / no lower bound'}",
        f"- Candidate count: {len(candidates)}",
        f"- Enabled sources checked: {packet['enabled_source_count']}",
        "",
        "## LLM Review Prompt",
        "",
        packet_prompt(),
        "",
    ]

    for priority in ("high", "medium", "low"):
        group = [candidate for candidate in candidates if candidate.priority == priority]
        if not group:
            continue
        lines.extend([f"## {priority.title()} Priority Candidates", ""])
        for candidate in group:
            lines.append(markdown_candidate(candidate))

    if failures:
        lines.extend(["## Source Failures", ""])
        for failure in failures:
            lines.append(f"- `{failure.source_id}` ({failure.url}): {failure.error}")
        lines.append("")

    if not candidates:
        lines.extend(["## No Candidates", "", "No new source items matched this scan window.", ""])

    return "\n".join(lines).rstrip() + "\n"


def write_packet(
    candidates: list[Candidate],
    failures: list[SourceFailure],
    *,
    since: datetime | None,
    enabled_source_count: int,
    runs_dir: Path,
) -> tuple[Path, Path]:
    generated_at = isoformat(now_utc())
    run_id = now_utc().strftime("%Y%m%d-%H%M%S")
    packet = {
        "generated_at": generated_at,
        "since": isoformat(since),
        "enabled_source_count": enabled_source_count,
        "candidates": [asdict(candidate) for candidate in candidates],
        "failures": [asdict(failure) for failure in failures],
    }
    runs_dir.mkdir(parents=True, exist_ok=True)
    json_path = runs_dir / f"{run_id}.json"
    markdown_path = runs_dir / f"{run_id}.md"
    write_json(json_path, packet)
    markdown_path.write_text(render_markdown_packet(packet), encoding="utf-8")
    return markdown_path, json_path


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_since(value: str | None, state: dict[str, Any]) -> tuple[datetime | None, bool]:
    if value:
        return parse_date(value), True
    last_success_at = state.get("last_success_at")
    if last_success_at:
        return parse_date(last_success_at), False
    return None, False


def command_scan(args: argparse.Namespace) -> int:
    sources_path = Path(args.sources)
    state_path = Path(args.state)
    runs_dir = Path(args.runs_dir)
    sources = load_sources(sources_path)
    enabled_sources = [source for source in sources if source.enabled]
    state = load_state(state_path)
    since, explicit_since = resolve_since(args.since, state)
    if args.since and since is None:
        print(f"Invalid --since value: {args.since}", file=sys.stderr)
        return 2

    candidates, failures, next_state = scan_sources(
        enabled_sources,
        state,
        since=since,
        explicit_since=explicit_since,
        limit_per_source=args.limit_per_source,
    )
    issue_refs: list[tuple[str, int]] = []
    for issue_ref in args.github_issue:
        try:
            issue_refs.append(parse_github_issue_ref(issue_ref, args.github_repo))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if issue_refs:
        with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(45.0)) as client:
            for repo, issue_number in issue_refs:
                try:
                    candidates.extend(
                        fetch_github_issue_candidates(
                            client,
                            repo,
                            issue_number,
                            since=since,
                            limit=args.github_issue_limit,
                        )
                    )
                except Exception as exc:  # noqa: BLE001 - failures are reported in the packet.
                    failures.append(
                        SourceFailure(
                            f"github-issue-{issue_number}",
                            f"{repo} issue #{issue_number}",
                            f"https://github.com/{repo}/issues/{issue_number}",
                            str(exc),
                        )
                    )

    candidates = dedupe_candidates(candidates)
    mark_recent_coverage(candidates, ROOT, args.coverage_months)
    markdown_path, json_path = write_packet(
        candidates,
        failures,
        since=since,
        enabled_source_count=len(enabled_sources) + len(issue_refs),
        runs_dir=runs_dir,
    )

    if not args.no_state_update:
        next_state["last_success_at"] = isoformat(now_utc())
        write_json(state_path, next_state)

    print(f"Markdown packet: {display_path(markdown_path)}")
    print(f"JSON packet: {display_path(json_path)}")
    print(f"Candidates: {len(candidates)}")
    if failures:
        print(f"Source failures: {len(failures)}", file=sys.stderr)
    return 1 if failures and args.fail_on_source_error else 0


def command_validate_sources(args: argparse.Namespace) -> int:
    sources = load_sources(Path(args.sources))
    enabled_count = sum(1 for source in sources if source.enabled)
    print(f"Validated {len(sources)} sources ({enabled_count} enabled).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Fetch sources and write a news packet")
    scan.add_argument("--sources", default=str(DEFAULT_SOURCES_PATH))
    scan.add_argument("--state", default=str(DEFAULT_STATE_PATH))
    scan.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    scan.add_argument("--since", help="Override state with a YYYY-MM-DD or ISO timestamp")
    scan.add_argument("--limit-per-source", type=int, default=30)
    scan.add_argument("--coverage-months", type=int, default=2)
    scan.add_argument("--github-repo", default=DEFAULT_GITHUB_REPO, help="Default owner/repo for numeric GitHub issue refs")
    scan.add_argument("--github-issue", action="append", default=[], help="Include a GitHub issue's comments as community topic candidates")
    scan.add_argument("--github-issue-limit", type=int, default=100)
    scan.add_argument("--no-state-update", action="store_true")
    scan.add_argument("--fail-on-source-error", action="store_true")
    scan.set_defaults(func=command_scan)

    validate = subparsers.add_parser("validate-sources", help="Validate source config")
    validate.add_argument("--sources", default=str(DEFAULT_SOURCES_PATH))
    validate.set_defaults(func=command_validate_sources)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
