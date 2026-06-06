#!/usr/bin/env python3
"""Strip universal base rules that now live in /assets/theme.css.

Targets the three universals added to assets/theme.css:

  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background:var(--bg); color:var(--tx); ...base props... }
  body::before { ...noise SVG... }

Strategy
--------
The * and body::before rules are stripped only when their normalised form
matches the canonical exactly.

The body rule is handled at the property level. Pages compare each body
declaration against the canonical set:

  - Declarations matching canonical exactly → removed.
  - Declarations not in canonical (e.g. slide pages' `display: flex`,
    `flex-direction: column`, `overflow-x: hidden`) → kept.

If a body rule has no declarations left after pruning, the whole rule is
dropped. Otherwise the rule is rewritten with just its bespoke
declarations.

Run modes
---------
  python3 tools/strip_canonical_base.py            # dry-run report
  python3 tools/strip_canonical_base.py --apply    # rewrite files
  python3 tools/strip_canonical_base.py --verbose  # show selectors per page
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


# --- Canonical fingerprints -------------------------------------------------

CANONICAL_RESET_PROPS = {
    "margin": "0",
    "padding": "0",
    "box-sizing": "border-box",
}

CANONICAL_BODY_PROPS = {
    "background": "var(--bg)",
    "color": "var(--tx)",
    "font-family": "'dm sans',sans-serif",
    "min-height": "100vh",
    "-webkit-font-smoothing": "antialiased",
}

CANONICAL_BODY_BEFORE_PROPS = {
    "content": '""',
    "position": "fixed",
    "inset": "0",
    "background-image": (
        "url(\"data:image/svg+xml,%3csvg viewbox='0 0 512 512' "
        "xmlns='http://www.w3.org/2000/svg'%3e%3cfilter id='n'%3e%3cfeturbulence "
        "type='fractalnoise' basefrequency='0.75' numoctaves='4' "
        "stitchtiles='stitch'/%3e%3c/filter%3e%3crect width='100%25' "
        "height='100%25' filter='url(%23n)' opacity='0.025'/%3e%3c/svg%3e\")"
    ),
    "pointer-events": "none",
    "z-index": "1000",
}


# --- CSS parsing ------------------------------------------------------------

def split_top_level_rules(css: str) -> list[tuple[str, str]]:
    """Yield (selector, body) pairs for each top-level rule.

    Same implementation as strip_canonical_chrome.py — handles balanced
    braces, skips /* comments */.
    """
    rules: list[tuple[str, str]] = []
    i = 0
    n = len(css)
    while i < n:
        while i < n and css[i].isspace():
            i += 1
        if i >= n:
            break
        if css.startswith("/*", i):
            end = css.find("*/", i + 2)
            i = (end + 2) if end != -1 else n
            continue
        brace = css.find("{", i)
        if brace == -1:
            break
        selector = css[i:brace]
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
            break
        body = css[brace + 1: j - 1]
        rules.append((selector, body))
        i = j
    return rules


def normalize_selector(sel: str) -> str:
    s = re.sub(r"/\*.*?\*/", "", sel, flags=re.DOTALL)
    s = re.sub(r"\s+", "", s)
    return s.lower()


def normalize_value(val: str) -> str:
    """Normalize a CSS value for comparison."""
    val = re.sub(r"/\*.*?\*/", "", val, flags=re.DOTALL)
    val = re.sub(r"\s+", " ", val).strip()
    # Strip spaces adjacent to commas/parens for stable comparison.
    val = re.sub(r"\s*,\s*", ",", val)
    val = re.sub(r"\s*\(\s*", "(", val)
    val = re.sub(r"\s*\)\s*", ")", val)
    return val.lower()


def parse_declarations(block: str) -> list[tuple[str, str]]:
    """Parse `prop: value; prop: value;` into a list of (prop, value) pairs.

    Honors balanced parens (url(...) etc.) and skips /* comments */.
    """
    decls: list[tuple[str, str]] = []
    s = re.sub(r"/\*.*?\*/", "", block, flags=re.DOTALL)
    # Split on ; not inside ()
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == ";" and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    for part in parts:
        if ":" not in part:
            continue
        prop, _, val = part.partition(":")
        prop = prop.strip().lower()
        if not prop:
            continue
        decls.append((prop, normalize_value(val)))
    return decls


# --- Per-page processing ----------------------------------------------------

STYLE_RE = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE)


def is_canonical_slide_page(text: str) -> bool:
    return "/assets/theme.css" in text


def declarations_match_canonical(
    decls: list[tuple[str, str]], canonical: dict[str, str]
) -> tuple[bool, list[tuple[str, str]]]:
    """Return (any_match, leftover_decls)."""
    leftover = []
    any_match = False
    for prop, val in decls:
        if prop in canonical and canonical[prop] == val:
            any_match = True
            continue
        leftover.append((prop, val))
    return any_match, leftover


def process_style(style_inner: str) -> tuple[str, dict]:
    rules = split_top_level_rules(style_inner)
    stripped_selectors: list[str] = []
    out_parts: list[str] = []

    pos = 0
    for sel, body in rules:
        rule_text_start = style_inner.find(sel, pos)
        if rule_text_start == -1:
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
        rule_end = j

        rule_text = style_inner[rule_text_start:rule_end]
        between = style_inner[pos:rule_text_start]
        sel_norm = normalize_selector(sel)
        decls = parse_declarations(body)

        action = None  # "drop" | "rewrite" | "keep"
        new_body_decls: list[tuple[str, str]] = []

        if sel_norm == "*":
            any_match, leftover = declarations_match_canonical(
                decls, CANONICAL_RESET_PROPS
            )
            if any_match and not leftover:
                action = "drop"
            elif any_match:
                action = "rewrite"
                new_body_decls = leftover

        elif sel_norm == "body::before":
            any_match, leftover = declarations_match_canonical(
                decls, CANONICAL_BODY_BEFORE_PROPS
            )
            if any_match and not leftover:
                action = "drop"

        elif sel_norm == "body":
            any_match, leftover = declarations_match_canonical(
                decls, CANONICAL_BODY_PROPS
            )
            if any_match and not leftover:
                action = "drop"
            elif any_match:
                action = "rewrite"
                new_body_decls = leftover

        if action == "drop":
            stripped_selectors.append(f"{sel_norm} (whole rule)")
            out_parts.append(_strip_to_comments(between))
        elif action == "rewrite":
            stripped_selectors.append(
                f"{sel_norm} (stripped canonical props, kept {len(new_body_decls)})"
            )
            out_parts.append(between)
            indent = _detect_indent(rule_text)
            decls_text = "; ".join(f"{p}:{v}" for p, v in new_body_decls)
            out_parts.append(f"{indent}{sel}{{{decls_text}}}")
        else:
            out_parts.append(between)
            out_parts.append(rule_text)

        pos = rule_end

    out_parts.append(style_inner[pos:])

    new_inner = "".join(out_parts)
    new_inner = re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", new_inner)
    return new_inner, {"stripped": stripped_selectors}


def _strip_to_comments(chunk: str) -> str:
    comments = re.findall(r"/\*.*?\*/", chunk, flags=re.DOTALL)
    if not comments:
        # Preserve a single newline so the next rule keeps reasonable spacing.
        return "\n" if "\n" in chunk else ""
    return "\n" + "\n".join(comments) + "\n"


def _detect_indent(rule_text: str) -> str:
    m = re.match(r"^([ \t]*)", rule_text)
    return m.group(1) if m else ""


def process_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not is_canonical_slide_page(text):
        return {"path": path, "skipped": "not linked to theme.css",
                "stats": None, "new_text": None}
    m = STYLE_RE.search(text)
    if not m:
        return {"path": path, "skipped": "no <style> block",
                "stats": None, "new_text": None}
    open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
    new_inner, stats = process_style(inner)
    if new_inner == inner:
        return {"path": path, "skipped": "no canonical base rules to strip",
                "stats": stats, "new_text": None}
    new_text = text[: m.start()] + open_tag + new_inner + close_tag + text[m.end():]
    return {"path": path, "skipped": None, "stats": stats, "new_text": new_text}


def targets() -> list[Path]:
    out: list[Path] = [ROOT / "index.html", ROOT / "about.html"]
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and MONTH_RE.match(child.name):
            for html in sorted(child.glob("*.html")):
                out.append(html)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    print(f"Stripping canonical base rules covered by assets/theme.css "
          f"(* reset, body base, body::before noise).\n")

    total_stripped = Counter()
    pages_modified = 0
    pages_skipped = 0

    for path in targets():
        result = process_page(path)
        rel = path.relative_to(ROOT)
        if result["skipped"]:
            pages_skipped += 1
            if args.verbose:
                print(f"  skip ({result['skipped']}): {rel}")
            continue
        stats = result["stats"]
        n_strip = len(stats["stripped"])
        if n_strip == 0:
            pages_skipped += 1
            continue
        pages_modified += 1
        for s in stats["stripped"]:
            total_stripped[s] += 1
        print(f"  {rel}: -{n_strip}  ({', '.join(stats['stripped'])})")
        if args.apply and result["new_text"]:
            path.write_text(result["new_text"], encoding="utf-8")

    print(f"\n{pages_modified} pages with strip opportunities, "
          f"{pages_skipped} pages skipped")
    print(f"Strip counts:")
    for sel, count in total_stripped.most_common():
        print(f"  {count:3d} ×  {sel}")
    if not args.apply:
        print("\n(dry-run — re-run with --apply to rewrite files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
