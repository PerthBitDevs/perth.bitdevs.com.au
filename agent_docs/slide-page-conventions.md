# Slide Page Conventions

Topic slide pages are the primary content format for monthly presentations (Feb 2026 onward). Each topic gets its own self-contained HTML file with slide-based navigation.

Start new slide pages from `templates/slide-deck.html.tmpl`. It is the canonical source for the current slide runtime, footer nav, Topics link pattern, accessible disclosure controls, CSS tokens, and TV-friendly scale.

## Contents

- [HTML Structure](#html-structure)
- [Required Behaviours](#required-behaviours)
- [Canonical Class Vocabulary](#canonical-class-vocabulary)
- [Navigation JavaScript](#navigation-javascript)
- [Content Components](#content-components)
- [Per-Topic Creativity](#per-topic-creativity)
- [When to Use Interactive Expandable Layouts](#when-to-use-interactive-expandable-layouts)
- [Non-Slide Topic Pages](#non-slide-topic-pages)

## HTML Structure

```html
<body>
  <!-- Fixed header -->
  <div class="header">
    <div class="badge">CATEGORY LABEL</div>
    <div class="dots" id="dots"></div>           <!-- Slide number buttons -->
    <a class="branding" href="/YYYY-MM/">← Topics</a>  <!-- Back link -->
  </div>

  <!-- Scrollable content area -->
  <div class="content">
    <div class="slide-inner">
      <div class="slide" data-name="Slide Name">
        <!-- Slide content: cards, boxes, grids, timelines -->
      </div>
      <!-- More slides... -->
    </div>
  </div>

  <!-- Fixed footer -->
  <div class="footer-nav">
    <button class="nav-btn" id="prevBtn">← Prev</button>
    <div class="nav-info" id="navInfo"></div>
    <button class="nav-btn next" id="nextBtn">Next →</button>
  </div>

  <script>/* Navigation JS */</script>
</body>
```

## Required Behaviours

### Keyboard navigation
- **ArrowRight** → next slide
- **ArrowLeft** → previous slide
- **Esc** → navigate back to month hub (`/YYYY-MM/`)

### Scroll fix
Body MUST use `overflow-x:hidden`, NOT `overflow:hidden`. This allows vertical scrolling when the user zooms in.

### Back link
The header branding area MUST be a link back to the month hub with text "← Topics".

### TV-friendly sizing (May 2026 onward)
Pages are projected on a 4K TV from a laptop via HDMI. New slide pages
MUST use the TV-friendly font scale and max-widths defined in
`design-system.md`. Do not retrofit older pages.

Quick reference:
- `h2.slide-title`: 36px (mobile 30px)
- `card-text`, `subtitle`, info/warn/box bodies: 20px
- box labels: 19px
- card-label, code, links, nav-btn: 17-19px
- `.slide-inner` max-width: 960px

## Canonical Class Vocabulary

New slide pages should use descriptive class names from `templates/slide-deck.html.tmpl`. Avoid the early shorthand dialect that appears in some historical pages.

| Role | Use | Legacy shorthand to avoid |
|------|-----|---------------------------|
| Slide viewport wrapper | `.content` | n/a |
| Slide width wrapper | `.slide-inner` | `.si` |
| Slide panel | `.slide` | n/a |
| Slide heading | `.slide-title` | `.st` |
| Card container | `.card` | n/a |
| Card label | `.card-label` | `.cl`, generic `.label` for slide cards |
| Card body text | `.card-text` | `.ct`, generic `.text` for slide cards |
| Supporting subtitle | `.subtitle` | n/a |
| Source link row | `.links` | n/a |
| Footer navigation | `.footer-nav`, `.nav-btn`, `.nav-info` | n/a |
| Dot navigation | `.dots`, `.dot` | n/a |

Do not mass-retrofit old pages only for naming. When editing an old slide page for a substantive content, accessibility, or validation reason, migrate shorthand classes in the touched area where it is practical and low risk. Preserve bespoke topic-specific classes for diagrams, timelines, stats, and simulations when those names describe the local visual model.

## Navigation JavaScript

The slide runtime is a single shared module: [`/assets/slides.js`](../assets/slides.js). It handles:

- ArrowLeft / ArrowRight between `.slide` elements (only initialises if `.slide` elements are present, so it's safe to load on auxiliary pages too)
- Dot rendering, click-to-jump, and prev/next button state
- `[data-disclosure-target]` disclosure toggling (aria-expanded + body hidden)
- **Escape → back to month hub**, derived from `location.pathname` — no more hardcoded `/YYYY-MM/` per page

Pages opt in with one line in `<head>`:

```html
<script src="/assets/slides.js" defer></script>
```

Canonical slide pages built from `templates/slide-deck.html.tmpl` inherit this automatically. If you need topic-specific behaviour (a custom diagram interaction, a stepper, layer disclosures like `mining-stack-miningos.html`), add another `<script>` block in the page — both will run.

To re-wire all canonical slide pages (e.g. after touching the template) run:

```bash
python3 tools/wire_slide_assets.py
```

It detects canonical pages by the inline-runtime signature, strips that runtime, and inserts the shared `<link>` + `<script>` tags. Idempotent. Bespoke pages without the signature (mining-stack-miningos, cluster-mempool-example, marmot-sloth-visualised, stepper-based aux pages) are skipped.

### Chrome CSS

The canonical slide-deck chrome — `.header`, `.badge`, `.badge-group`, `.update-tag`, `.dots`, `.dot`, `.branding`, `.content`, `.slide-inner`, `.slide`, `h2.slide-title`, `.subtitle`, `.hero`, `.hero-kicker`, `.hero-text`, `.grid`, `.card` plus colour variants, `.card-label`, `.card-text`, `.links`, `.disclosure*`, `.footer-nav`, `.nav-btn`, `.nav-info`, plus the `@media(max-width:760px)` responsive rules — lives in [`/assets/slide-chrome.css`](../assets/slide-chrome.css). Loaded by every canonical slide page via:

```html
<link rel="stylesheet" href="/assets/slide-chrome.css">
```

Per-page `<style>` blocks load *after* the shared chrome, so topic pages can still override or extend any rule with bespoke topic components. Existing slide pages had their inline copies of canonical rules stripped by `tools/strip_canonical_chrome.py` — only rules whose normalized form matched the canonical exactly were removed. Per-month bespoke variants (notably the pre-May-2026 tighter font scales) and per-topic overrides survive untouched, so pages render exactly as they did before the carve-out.

The strip tool can be re-run anytime:

```bash
python3 tools/strip_canonical_chrome.py            # dry-run report
python3 tools/strip_canonical_chrome.py --apply    # rewrite files
python3 tools/strip_canonical_chrome.py --verbose  # show selectors per page
```

If `/assets/slide-chrome.css` ever changes, run the dry-run to discover new exact-match opportunities.

## Content Components

Reusable building blocks within slides (all defined inline per page):

| Component | Class | Purpose |
|-----------|-------|---------|
| Info card | `.card` | General content block with label + text |
| Alert/highlight box | `.box` | Colored background box (warning, info, success) |
| Two-column layout | `.cols` | Side-by-side comparison |
| Rule grid | `.rule-grid` | 2x2 grid of numbered items |
| Timeline | `.tl-item` | Vertical timeline with dots and lines |
| Big stat | `.big-stat` / `.stat` | Large number display |
| Signal bar | `.signal-bar` | Centered stat with subtitle |
| Table | `.tbl` | Data table with mono headers |

## Per-Topic Creativity

Each topic can have bespoke design elements — the slide format is a framework, not a straitjacket. Examples from Feb 2026:

- **BIP-110**: Rule grid, timeline, signal bar
- **Mining Stack**: No slides at all — interactive expandable layers with a stack diagram
- **OpenClaw**: Two-column layout, stat row with 4 stats
- **Wallet Bug**: Timeline + big stat trio

The common thread is the canonical token system (dark + Bitcoin-orange palette, semantic accents, JBM/DM-Sans), the slide chrome (header, dots, footer-nav), and the navigation pattern. Content layout is free-form.

Bespoke means **layouts and accent choices inside the canonical system** — not swapping the whole aesthetic for one topic (no cream-paper hand-lettered zines, no cyberpunk-neon decks). The global light/dark toggle (see `design-system.md`) is orthogonal to this rule: it is a site-wide user preference applied uniformly via the shared `/assets/theme.css` module, not a per-topic aesthetic choice.

## When to Use Interactive Expandable Layouts

The mining stack MiningOS page (`2026-02/mining-stack-miningos.html`) is a strong reference for topics that benefit from **layered, expandable sections** rather than linear slides. Use this format when:

- The topic has a **hierarchical or stacked structure** (layers, levels, components)
- Users benefit from **seeing the whole picture first** then drilling into detail
- Content is better explored non-linearly (users may only care about certain layers)
- The topic involves **comparing multiple items at the same level** (e.g. firmware options, pool choices)

Key patterns from the MiningOS page:
- Collapsible layer cards where the visible header row is a real `<button type="button">`
- Disclosure buttons must set `aria-expanded`, point `aria-controls` at the collapsible body, and keep `aria-expanded` synced whenever the `.open` state changes
- Do not put `onclick` on a plain `<div>` for disclosure controls; keyboard users and screen readers need a button or native `<details>/<summary>`
- Stack connectors between layers showing protocols/interfaces
- Color-coded layers (each layer has its own semantic color)
- One layer starts open (the most important one) to draw attention
- Highlight callout with glowing border for the focal point
- Example configurations at the bottom showing how layers combine

## Non-Slide Topic Pages

Some topics work better without slides (e.g. the mining stack explainer). These pages:
- Use a regular scrollable layout (no `.slide` classes)
- Still MUST have Esc key → back to month hub
- Still MUST have a visible "← Topics" back link
- Still use the same color palette and typography

For visual explainers or step-through pages that are not slide decks, start from `templates/auxiliary-visual-page.html.tmpl` and list the page under `auxiliary_pages` in the month manifest when the month has one.
