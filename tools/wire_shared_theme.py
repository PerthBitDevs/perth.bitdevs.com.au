#!/usr/bin/env python3
"""Wire every HTML page (and template) to load the shared /assets/theme module.

Two responsibilities:
  1. Strip artefacts left by the earlier inline patcher (tools/apply_light_mode.py):
     the inlined `html[data-theme="light"]` overrides, the inlined
     `.theme-toggle` CSS, the inlined `#themeToggle` <button>, and the inlined
     toggle-click <script>.
  2. Insert the shared-theme wiring on every page that doesn't already have it:
       - FOUC-prevention <script> (must run before stylesheet apply, hence inline)
       - <link rel="stylesheet" href="/assets/theme.css">
       - <script src="/assets/theme.js" defer></script>

Idempotent: re-running is a no-op once each page links the shared assets and
has no leftover inline theme markers.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

LINK_MARKER = '/assets/theme.css'
JS_MARKER = '/assets/theme.js'
FOUC_MARKER = "localStorage.getItem('pbd-theme')"

FOUC_SCRIPT = (
    "<script>(function(){try{var s=localStorage.getItem('pbd-theme');"
    "var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)');"
    "var t=s||(m&&m.matches?'light':'dark');"
    "document.documentElement.dataset.theme=t}catch(e){}})();</script>"
)
LINK_TAG = '<link rel="stylesheet" href="/assets/theme.css">'
SCRIPT_TAG = '<script src="/assets/theme.js" defer></script>'

FONTS_LINK_RE = re.compile(
    r'<link href="https://fonts\.googleapis\.com[^"]+" rel="stylesheet">'
)

# --- Stale artefacts from tools/apply_light_mode.py that this cutover removes.
# The inline FOUC is intentionally NOT stripped — its content matches the new
# canonical FOUC exactly, so re-inserting it would be a no-op churn. The
# canonical FOUC is the same one the patcher wrote, just reframed as canonical.

LEGACY_TOGGLE_JS_RE = re.compile(
    r"\n?<script>\(function\(\)\{var b=document\.getElementById\('themeToggle'\);"
    r".*?</script>",
    re.DOTALL,
)
LEGACY_TOGGLE_BUTTON_RE = re.compile(
    r"<button class=\"theme-toggle\" id=\"themeToggle\"[^>]*>.*?</button>\n?",
    re.DOTALL,
)

# Inline CSS lines injected by the earlier patcher. Each line ends with \n.
LEGACY_LIGHT_BLOCK_LINES = [
    re.compile(r"^\s*html\[data-theme=\"light\"\]\{--bg:#f7f4ec;[^\n]*\n", re.M),
    re.compile(r"^\s*html\[data-theme=\"light\"\] \.glow\{opacity:\.55\}\n", re.M),
    re.compile(
        r"^\s*html\[data-theme=\"light\"\] h1\{background:linear-gradient[^\n]*\n",
        re.M,
    ),
    re.compile(
        r"^\s*html\[data-theme=\"light\"\] a\.event:hover,[^\n]*\n",
        re.M,
    ),
    re.compile(r"^\s*\.theme-toggle\{position:fixed;top:16px;right:16px[^\n]*\n", re.M),
    re.compile(r"^\s*\.theme-toggle:hover\{[^\n]*\n", re.M),
    re.compile(r"^\s*\.theme-toggle svg\{[^\n]*\n", re.M),
    re.compile(r"^\s*\.theme-toggle \.icon-sun,\.theme-toggle \.icon-moon\{[^\n]*\n", re.M),
    re.compile(r"^\s*html\[data-theme=\"dark\"\] \.theme-toggle \.icon-sun\{[^\n]*\n", re.M),
    re.compile(r"^\s*html\[data-theme=\"light\"\] \.theme-toggle \.icon-moon\{[^\n]*\n", re.M),
    re.compile(r"^\s*@media print\{\.theme-toggle\{display:none\}\}\n", re.M),
]


def strip_legacy(text: str) -> str:
    """Remove the per-page artefacts the inline patcher injected.

    Does NOT strip the FOUC script: its content matches the canonical FOUC
    we want to leave in place exactly, so stripping and re-adding would just
    churn the diff.
    """
    text = LEGACY_TOGGLE_JS_RE.sub("", text)
    text = LEGACY_TOGGLE_BUTTON_RE.sub("", text)
    for pat in LEGACY_LIGHT_BLOCK_LINES:
        text = pat.sub("", text)
    return text


def insert_wiring(text: str) -> str:
    """Ensure FOUC script + theme.css link + theme.js script are present.

    Each piece is checked independently — pages that already have one but not
    the others get the missing pieces inserted at the canonical anchor.
    Anchor: immediately after the canonical Google Fonts <link>; falls back to
    immediately before </head> (for pages that use @import inside <style>).
    """
    has_fouc = FOUC_MARKER in text
    has_link = LINK_MARKER in text
    has_js = JS_MARKER in text
    if has_fouc and has_link and has_js:
        return text

    parts = []
    if not has_fouc:
        parts.append(FOUC_SCRIPT)
    if not has_link:
        parts.append(LINK_TAG)
    if not has_js:
        parts.append(SCRIPT_TAG)
    insertion = "\n" + "\n".join(parts)

    m = FONTS_LINK_RE.search(text)
    if m:
        return text[: m.end()] + insertion + text[m.end():]

    head_close = text.find("</head>")
    if head_close == -1:
        raise RuntimeError("could not find Google Fonts <link> or </head>")
    return text[:head_close] + insertion + "\n" + text[head_close:]


def patch(text: str) -> tuple[str, bool]:
    original = text
    text = strip_legacy(text)
    text = insert_wiring(text)
    return text, text != original


def targets() -> list[Path]:
    out: list[Path] = []
    # Root navigation pages
    out.append(ROOT / "index.html")
    out.append(ROOT / "about.html")
    # Month hubs and slide/topic pages
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and MONTH_RE.match(child.name):
            out.extend(sorted(child.glob("*.html")))
    # Templates
    out.append(ROOT / "templates" / "month-hub.html.tmpl")
    out.append(ROOT / "templates" / "archive-page.html.tmpl")
    out.append(ROOT / "templates" / "slide-deck.html.tmpl")
    out.append(ROOT / "templates" / "auxiliary-visual-page.html.tmpl")
    return out


def main() -> int:
    changed = 0
    unchanged = 0
    for path in targets():
        if not path.exists():
            print(f"missing: {path.relative_to(ROOT)}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        new, did = patch(text)
        if did:
            path.write_text(new, encoding="utf-8")
            print(f"wired: {path.relative_to(ROOT)}")
            changed += 1
        else:
            print(f"skip (already wired): {path.relative_to(ROOT)}")
            unchanged += 1
    print(f"\n{changed} wired, {unchanged} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
