# Perth BitDevs Website

Static HTML site for [perth.bitdevs.com.au](https://perth.bitdevs.com.au). No build step, no frameworks. GitHub Pages deployment via push to `master`.

## Stack

- Pure static HTML + per-page inline CSS + small shared `/assets/` theme module
- GitHub Pages with `.nojekyll` (no build)
- Google Fonts: JetBrains Mono (headings/mono), DM Sans (body)
- No deployed runtime dependencies, no package manager, no build tools

## Structure

```
/                   Landing page (event hub)
/about.html         About & rules
/YYYY-MM/           Monthly event folder
  manifest.json     Current-month event/topic metadata source of truth
  index.html        Month hub (links to topic pages, or archive of topics)
  topic-name.html   Individual topic slides (Feb 2026+ only)
/assets/            Shared static deps
  theme.css         Light-mode token overrides + theme-toggle component (every page)
  theme.js          Theme toggle handler — FOUC-prevention script stays inline per page (every page)
  slide-chrome.css  Canonical slide-deck chrome (.header/.dots/.slide/.footer-nav/etc.) — canonical slide pages
  slides.js         Slide runtime + disclosure handler + Escape→month (canonical slide pages)
/templates/         Authoring templates copied into month folders; not deployed directly
  manifest.json.tmpl
  *.html.tmpl
```

## Local Tooling

- `just dev` and `just run` serve the static site without requiring the newswatch `.venv`.
- `tools/site_check.py` validates static-site contracts without network access.
- `tools/newswatch/` is optional local planning tooling. It uses Python dependencies installed into `.venv` and writes ignored research packets under `tools/newswatch/runs/`.
- Local tooling is not part of the deployed GitHub Pages runtime.

## Commands

- `just dev [port=8888]` - serve the static site locally
- `just run [port=8888]` - serve locally, wait until ready, then open the browser; choose another port with `just run port=8889`
- `just site-check` - validate local links, manifest consistency, slide conventions, and safety warnings
- `just check` - run `site-check`, newswatch source validation, and newswatch tests
- `just setup-newswatch` - create `.venv` and install newswatch dependencies
- `just news-scan since=YYYY-MM-DD issue=NN` - create a local planning packet from curated sources and the meetup issue
- `just news-scan-preview since=YYYY-MM-DD issue=NN` - create a planning packet without advancing the local newswatch cursor

## Content Types

1. **Interactive slide pages** (2026-02 onward): Per-topic HTML with slide navigation, keyboard controls, bespoke creative design per topic
2. **Archive pages** (2023-12 through 2025-12): Single scrollable page per month listing all topics from the GitHub issue

## Theming

Every page — landing, about, month hubs, archives, slide decks, auxiliary visual pages — carries a light/dark theme toggle. Dark + Bitcoin-orange is the canonical default; light mode is an inverse warm-paper palette opted into via `data-theme="light"` on `<html>`. The preference is stored in `localStorage` under `pbd-theme` and the initial value falls back to `prefers-color-scheme`.

The theme system is a single shared module:

- `/assets/theme.css` — light-mode token overrides + `.theme-toggle` component CSS
- `/assets/theme.js` — toggle button construction + click handler

Each page loads them via three head-level tags inserted right after the Google Fonts `<link>`:

```html
<script>(function(){try{var s=localStorage.getItem('pbd-theme');var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)');var t=s||(m&&m.matches?'light':'dark');document.documentElement.dataset.theme=t}catch(e){}})();</script>
<link rel="stylesheet" href="/assets/theme.css">
<script src="/assets/theme.js" defer></script>
```

The FOUC-prevention script stays inline because it must run before the stylesheet applies. Per-page inline `:root` token defaults remain — the shared module only carries the variations on top.

When adding a new page, copy these three tags from `templates/month-hub.html.tmpl` (or any other template). To backfill the wiring across all pages run `python3 tools/wire_shared_theme.py` (idempotent). See `agent_docs/design-system.md` for the light palette and toggle behaviour.

## Source Templates

- Start new manifests, month hubs, slide decks, archive pages, and auxiliary visual pages from `templates/`.
- Template files use `.html.tmpl` or `.json.tmpl` so placeholder values are not treated as published pages.
- After copying a template into `YYYY-MM/`, replace every `{{PLACEHOLDER}}` and keep the published HTML self-contained.
- Current-month auxiliary pages must be listed in `manifest.json` with `parent_topic` pointing at the owning topic file.
- Do not copy last month's closest page by eye unless the template is genuinely the wrong page type.

## Monthly Workflow

1. Community submits topics as comments on the GitHub issue at `PerthBitDevs/PerthBitDevs`
2. Before the meetup, topic slide HTML is created with Claude Code from the tracked templates (see `agent_docs/content-workflow.md`)
3. For current/upcoming months, update `YYYY-MM/manifest.json` before editing hub or landing HTML
4. Files go into `/YYYY-MM/` directory
5. Landing page `index.html` updated with new event entry
6. Run `just site-check` or `just check`
7. Push to `master` deploys

## Key Constraints

- Pages depend ONLY on: Google Fonts, `/assets/theme.{css,js}` (every page), and `/assets/slide-chrome.css` + `/assets/slides.js` (canonical slide pages only). All other CSS and JS stays inline per page (per-topic creative freedom). No build step. No framework.
- New page work should start from `templates/`, then be edited in the target month directory.
- Current-month non-topic HTML pages must be classified under `auxiliary_pages` in `manifest.json`; historical non-manifest exceptions are documented in `agent_docs/content-workflow.md`.
- New slide pages should use the canonical class vocabulary in `agent_docs/slide-page-conventions.md`; avoid old shorthand names such as `.si`, `.st`, `.cl`, and `.ct`.
- Presentation context: **slides are projected on a 4K TV via HDMI from a laptop.** Use the TV-friendly font scale and max-widths in `agent_docs/design-system.md` for all new slide pages.
- Slide pages MUST use `overflow-x:hidden` on body, NOT `overflow:hidden` (allows vertical scroll when zoomed)
- Slide pages MUST handle **Esc key** → navigate back to month hub
- Slide pages MUST have a visible **"← Topics" back link** in the header
- Topic filenames: kebab-case (`bip-110.html`, `private-tx-broadcast.html`)
- Directory names: `YYYY-MM` format

## Destructive Actions (Topic Files)

**Before deleting any `YYYY-MM/*.html` file, confirm with the user.** Topic file deletion is not reversible from git history alone if the file was uncommitted. May 2026 lost `ecash-hardfork.html` during a consolidation pass and required Time Machine recovery. This rule applies to:

- File deletion (`rm`, `git rm`, equivalent)
- Renames that lose content (treat as delete + create)
- Topic merges that drop a file (confirm the merge target is correct first)

Editing or rewriting a file in place is fine. The constraint is only on losing the file.

## Deep Dive Documentation

See `agent_docs/` for detailed references:

- `design-system.md` — Colors, typography, CSS variables, component patterns
- `slide-page-conventions.md` — Slide HTML structure, JS navigation, required behaviours
- `content-workflow.md` — GitHub issue → slide HTML pipeline (incl. fact-check gate, multi-agent coordination)
- `voice-and-tone.md` — Banned phrases, bullets-vs-prose, neutrality, before/after rewrites
- `content-budget.md` — Per-meetup topic count, slides per deck, cut-order priorities
- `templates/` - Tracked copy sources for new monthly content

### Refreshing Docs

`agent_docs/.docs-ref` stores the commit hash docs were last validated against.
To see code changes since: `git diff $(cat agent_docs/.docs-ref)..HEAD -- ':!agent_docs'`
After updating docs, set `.docs-ref` to the current commit.
