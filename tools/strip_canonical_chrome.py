#!/usr/bin/env python3
"""Strip inline chrome rules that exactly duplicate /assets/slide-chrome.css.

Approach
--------
For each canonical slide page:

  1. Extract the inline <style>...</style> block.
  2. Iterate through its top-level CSS rules. Each rule is either:
       - a regular declaration block:  selector { declarations }
       - an at-rule block (we only care about @media): @media (...) { ... }
  3. For each rule, compute a canonical normalized form (whitespace,
     casing, optional trailing semicolons collapsed).
  4. Compare against the precomputed set of normalized canonical rules
     extracted from assets/slide-chrome.css.
  5. Strip exact matches. Leave divergent rules alone — those are
     intentional per-topic overrides (especially the pre-May-2026 smaller
     font scales).
  6. Re-emit the cleaned <style> block.

Run modes
---------
  python3 tools/strip_canonical_chrome.py            # dry-run report
  python3 tools/strip_canonical_chrome.py --apply    # rewrite files
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
CANONICAL_CSS = ROOT / "assets" / "slide-chrome.css"
RUNTIME_SIGNATURE = "document.querySelectorAll('.slide')"


# --- CSS rule parsing -------------------------------------------------------

def split_top_level_rules(css: str) -> list[tuple[str, str]]:
    """Yield (selector_or_at_rule_header, body) pairs for each top-level rule.

    Handles balanced braces (for @media and similar nested blocks). Skips
    /* comments */. Strings ('...', "...") are NOT navigated (we don't have
    any in the chrome) — if you add CSS strings, extend this parser.
    """
    rules: list[tuple[str, str]] = []
    i = 0
    n = len(css)
    while i < n:
        # Skip whitespace
        while i < n and css[i].isspace():
            i += 1
        if i >= n:
            break
        # Skip comments
        if css.startswith("/*", i):
            end = css.find("*/", i + 2)
            i = (end + 2) if end != -1 else n
            continue
        # Read selector / at-rule header up to '{'
        brace = css.find("{", i)
        if brace == -1:
            break
        selector = css[i:brace]
        # Find matching '}'
        depth = 1
        j = brace + 1
        while j < n and depth > 0:
            c = css[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        if depth != 0:
            # malformed — give up
            break
        body = css[brace + 1: j - 1]
        rules.append((selector, body))
        i = j
    return rules


def normalize_chunk(s: str) -> str:
    """Whitespace-normalize a CSS fragment.

    - Strip /* comments */
    - Collapse runs of whitespace to single spaces
    - Remove spaces adjacent to {, }, ;, :, ,, (, )
    - Lowercase property names and selectors (color hex values stay as written)
    - Drop trailing ; before }
    """
    # Strip comments
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    # Normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # Remove spaces adjacent to syntax tokens
    for tok in "{};:,()":
        s = s.replace(" " + tok, tok).replace(tok + " ", tok)
    # Drop trailing ;
    s = re.sub(r";+\}", "}", s)
    s = re.sub(r";+$", "", s)
    # Lowercase selector / property side, but preserve var() / hex values:
    # we don't differentiate, just lowercase the whole thing — chrome rules
    # already use lowercase hex.
    return s.lower()


def normalize_rule(selector: str, body: str) -> str:
    sel = normalize_chunk(selector)
    bod = normalize_chunk(body)
    return f"{sel}{{{bod}}}"


# --- Canonical extraction ---------------------------------------------------

def load_canonical_rules() -> set[str]:
    css = CANONICAL_CSS.read_text(encoding="utf-8")
    rules = split_top_level_rules(css)
    normalized: set[str] = set()
    nested: set[str] = set()
    for sel, body in rules:
        sel_n = normalize_chunk(sel)
        if sel_n.startswith("@media"):
            inner = split_top_level_rules(body)
            inner_norm = "".join(normalize_rule(s, b) for s, b in inner)
            normalized.add(f"{sel_n}{{{inner_norm}}}")
            # Also accept the inner block as a whole (some pages have the
            # same media block but with reformatted whitespace).
            nested.add(sel_n)
        else:
            normalized.add(normalize_rule(sel, body))
    return normalized


# --- Per-page processing ----------------------------------------------------

STYLE_RE = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE)


def is_canonical_slide_page(text: str) -> bool:
    """Same definition as wire_slide_assets.py — has the slide signature."""
    # After stage 2 the inline runtime is gone, so detect by the assets link.
    return "/assets/slides.js" in text


def process_style(style_inner: str, canonical: set[str]) -> tuple[str, dict]:
    """Return (new_style_inner, stats)."""
    rules = split_top_level_rules(style_inner)
    stripped: list[str] = []
    kept_div: list[str] = []
    out_parts: list[str] = []

    # We want to keep the page's original formatting where possible. For
    # each rule we re-emit the original text. If a rule is stripped we drop
    # it (and any immediately following blank line).
    pos = 0
    for sel, body in rules:
        # Find the original span of this rule in style_inner
        # Re-search from pos for the selector text
        rule_text_start = style_inner.find(sel, pos)
        if rule_text_start == -1:
            # Defensive fallback — skip
            continue
        brace_open = style_inner.find("{", rule_text_start)
        depth = 1
        j = brace_open + 1
        while j < len(style_inner) and depth > 0:
            c = style_inner[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        rule_end = j  # index after matching '}'

        rule_text = style_inner[rule_text_start:rule_end]
        between = style_inner[pos:rule_text_start]
        normalized = normalize_rule(sel, body)

        if normalized in canonical:
            stripped.append(normalize_chunk(sel))
            # Drop both the between-text (whitespace/comments) and the rule.
            # We still emit between's comments though.
            out_parts.append(_strip_to_comments(between))
        else:
            sel_n = normalize_chunk(sel)
            # Did the selector exist in canonical but with different body?
            if any(c.startswith(sel_n + "{") for c in canonical):
                kept_div.append(sel_n)
            out_parts.append(between)
            out_parts.append(rule_text)

        pos = rule_end

    # Trailing tail (whitespace/comments after last rule)
    out_parts.append(style_inner[pos:])

    new_inner = "".join(out_parts)
    # Collapse 3+ consecutive blank lines to 2
    new_inner = re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", new_inner)
    return new_inner, {"stripped": stripped, "kept_divergent": kept_div}


def _strip_to_comments(chunk: str) -> str:
    """Keep only /* comments */ from a whitespace chunk; drop the whitespace."""
    comments = re.findall(r"/\*.*?\*/", chunk, flags=re.DOTALL)
    if not comments:
        return ""
    return "\n" + "\n".join(comments) + "\n"


def process_page(path: Path, canonical: set[str]) -> dict:
    text = path.read_text(encoding="utf-8")
    if not is_canonical_slide_page(text):
        return {"path": path, "skipped": "not canonical", "stats": None,
                "new_text": None}
    m = STYLE_RE.search(text)
    if not m:
        return {"path": path, "skipped": "no <style> block",
                "stats": None, "new_text": None}
    open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
    new_inner, stats = process_style(inner, canonical)
    if new_inner == inner:
        return {"path": path, "skipped": "no canonical rules found",
                "stats": stats, "new_text": None}
    new_text = text[: m.start()] + open_tag + new_inner + close_tag + text[m.end():]
    return {"path": path, "skipped": None, "stats": stats, "new_text": new_text}


def targets() -> list[Path]:
    out: list[Path] = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and MONTH_RE.match(child.name):
            for html in sorted(child.glob("*.html")):
                if html.name == "index.html":
                    continue
                out.append(html)
    return out


# --- Main -------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Rewrite files. Default is dry-run.")
    ap.add_argument("--verbose", action="store_true",
                    help="Print stripped + divergent rule selectors per page.")
    args = ap.parse_args()

    canonical = load_canonical_rules()
    print(f"Loaded {len(canonical)} canonical rule fingerprints "
          f"from {CANONICAL_CSS.relative_to(ROOT)}\n")

    total_stripped = Counter()
    total_kept_divergent = Counter()
    pages_modified = 0
    pages_skipped = 0

    for path in targets():
        result = process_page(path, canonical)
        rel = path.relative_to(ROOT)
        if result["skipped"]:
            pages_skipped += 1
            if args.verbose:
                print(f"  skip ({result['skipped']}): {rel}")
            continue
        stats = result["stats"]
        n_strip = len(stats["stripped"])
        n_div = len(stats["kept_divergent"])
        if n_strip == 0:
            pages_skipped += 1
            if args.verbose:
                print(f"  no matches: {rel}")
            continue

        pages_modified += 1
        total_stripped.update(stats["stripped"])
        total_kept_divergent.update(stats["kept_divergent"])
        print(f"  {rel}: -{n_strip} stripped, {n_div} divergent kept")
        if args.verbose:
            for s in stats["stripped"]:
                print(f"      -  {s}")
            for s in stats["kept_divergent"]:
                print(f"      ~  {s}  (kept — declarations differ)")
        if args.apply and result["new_text"]:
            path.write_text(result["new_text"], encoding="utf-8")

    print(f"\n{pages_modified} pages with strip opportunities, "
          f"{pages_skipped} pages skipped")
    print(f"Top stripped rules:")
    for sel, count in total_stripped.most_common(10):
        print(f"  {count:3d} ×  {sel}")
    print(f"Top divergent rules (kept as-is):")
    for sel, count in total_kept_divergent.most_common(10):
        print(f"  {count:3d} ×  {sel}")
    if not args.apply:
        print("\n(dry-run — re-run with --apply to rewrite files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
