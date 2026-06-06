#!/usr/bin/env python3
"""Wire canonical slide-deck pages to /assets/slide-chrome.css and slides.js.

A "canonical slide page" is identified by the presence of the inline runtime
signature `document.querySelectorAll('.slide')`. Bespoke pages without that
signature (mining-stack-miningos, cluster-mempool-example, marmot-sloth-
visualised, auxiliary visual pages) are left alone — they manage their own
chrome and runtime.

For canonical pages this script:
  1. Inserts <link rel="stylesheet" href="/assets/slide-chrome.css"> after
     the theme.css link.
  2. Inserts <script src="/assets/slides.js" defer></script> after the
     theme.js script.
  3. Strips the inline canonical runtime <script>...</script> block.

The inline chrome CSS is intentionally left inline on existing pages — the
shared CSS loads before it so per-page inline rules continue to override,
making the cutover behaviorally safe. Future pages built from the updated
slide-deck.html.tmpl simply don't carry the inline chrome.

Idempotent: re-running is a no-op once a page links both shared assets and
no longer carries the inline runtime.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

RUNTIME_SIGNATURE = "document.querySelectorAll('.slide')"
CHROME_LINK = '<link rel="stylesheet" href="/assets/slide-chrome.css">'
SLIDES_SCRIPT = '<script src="/assets/slides.js" defer></script>'

THEME_LINK_RE = re.compile(
    r'<link rel="stylesheet" href="/assets/theme\.css">'
)
THEME_JS_RE = re.compile(
    r'<script src="/assets/theme\.js" defer></script>'
)

# The inline canonical runtime is a <script>...</script> block whose body
# references `.slide` querying. Match non-greedily across the block.
INLINE_RUNTIME_RE = re.compile(
    r"\n?<script>(?:(?!</script>).)*?document\.querySelectorAll\('\.slide'\)"
    r"(?:(?!</script>).)*?</script>\n?",
    re.DOTALL,
)


def is_canonical_slide_page(text: str) -> bool:
    return RUNTIME_SIGNATURE in text


def insert_after(text: str, pattern: re.Pattern[str], snippet: str) -> str:
    if snippet in text:
        return text
    m = pattern.search(text)
    if not m:
        raise RuntimeError(
            f"could not find anchor to insert: {snippet!r}"
        )
    return text[: m.end()] + "\n" + snippet + text[m.end():]


def patch(text: str) -> tuple[str, bool]:
    if not is_canonical_slide_page(text):
        return text, False

    original = text
    text = insert_after(text, THEME_LINK_RE, CHROME_LINK)
    text = insert_after(text, THEME_JS_RE, SLIDES_SCRIPT)
    text = INLINE_RUNTIME_RE.sub("", text)
    return text, text != original


def targets() -> list[Path]:
    out: list[Path] = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and MONTH_RE.match(child.name):
            for html in sorted(child.glob("*.html")):
                if html.name == "index.html":
                    continue
                out.append(html)
    return out


def main() -> int:
    canonical = 0
    skipped_bespoke = 0
    unchanged_canonical = 0
    for path in targets():
        text = path.read_text(encoding="utf-8")
        if not is_canonical_slide_page(text):
            print(f"skip (bespoke, no inline slide runtime): "
                  f"{path.relative_to(ROOT)}")
            skipped_bespoke += 1
            continue
        new, did = patch(text)
        if did:
            path.write_text(new, encoding="utf-8")
            print(f"wired: {path.relative_to(ROOT)}")
            canonical += 1
        else:
            print(f"skip (already wired): {path.relative_to(ROOT)}")
            unchanged_canonical += 1
    print(
        f"\n{canonical} canonical wired, "
        f"{unchanged_canonical} canonical already wired, "
        f"{skipped_bespoke} bespoke skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
