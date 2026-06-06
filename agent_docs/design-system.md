# Design System

## Contents

- [Color Palette](#color-palette)
- [Light Mode](#light-mode)
- [Typography](#typography)
- [Google Fonts Import](#google-fonts-import)
- [Shared Visual Elements](#shared-visual-elements)
- [Page Max Widths](#page-max-widths)
- [Responsive Breakpoints](#responsive-breakpoints)

## Color Palette

All pages use CSS custom properties. The canonical set:

```css
:root {
  /* Backgrounds */
  --bg: #06080d;        /* Page background */
  --sf: #0d1117;        /* Surface (cards) */
  --sf2: #151b25;       /* Surface elevated (hover states) */
  --bd: #1c2432;        /* Border default */
  --bdh: #2a3545;       /* Border hover */

  /* Text */
  --tx: #e2e8f0;        /* Primary text */
  --txM: #94a3b8;       /* Muted text (descriptions) */
  --txD: #506078;       /* Dim text (metadata, dates) */

  /* Accent — Bitcoin orange */
  --or: #f7931a;        /* Primary accent */
  --orD: rgba(247,147,26,.10);  /* Orange background tint */
  --orG: rgba(247,147,26,.25);  /* Orange glow */
  --orB: #b36a0f;       /* Orange border (darker) */

  /* Semantic colors */
  --bl: #3b82f6;        /* Blue — governance, info */
  --gn: #22c55e;        /* Green — positive, resolution */
  --rd: #ef4444;        /* Red — critical, warnings, bugs */
  --cy: #06b6d4;        /* Cyan — privacy */
  --pu: #a855f7;        /* Purple — pool, technical */
  --pk: #ec4899;        /* Pink — AI, security */
  --yl: #eab308;        /* Yellow — highlights */
  --tl: #14b8a6;        /* Teal — mining (Tether green) */
}
```

Each semantic color has a dim variant at ~12% opacity for backgrounds (e.g. `--bld: rgba(59,130,246,.12)`).

## Light Mode

Dark + Bitcoin-orange is the canonical default. Every page — landing, about, month hubs, archives, slide decks, auxiliary visual pages — supports a user-toggleable light mode via `data-theme="light"` on `<html>`. The light palette is warm-paper inverse: cream background, white card surfaces, darker orange text accents for AA contrast.

### Where the theme lives

The light overrides and toggle component are NOT inlined per page. They live in a single shared module:

- [`/assets/theme.css`](../assets/theme.css) — `html[data-theme="light"]` token overrides and slide-page-specific tweaks (gradient h1, slide-title gradient, hero-text strong colour), plus the `.theme-toggle` button styles
- [`/assets/theme.js`](../assets/theme.js) — toggle button construction (sun/moon SVGs, no emoji), click handler, localStorage persistence

Per-page inline `:root { ... }` blocks still define the dark token defaults. The shared `theme.css` only supplies the `[data-theme="light"]` overrides on top — attribute-selector specificity ensures the override wins over inline `:root`.

### Per-page wiring

Three head-level tags inserted immediately after the Google Fonts `<link>`:

```html
<script>(function(){try{var s=localStorage.getItem('pbd-theme');var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)');var t=s||(m&&m.matches?'light':'dark');document.documentElement.dataset.theme=t}catch(e){}})();</script>
<link rel="stylesheet" href="/assets/theme.css">
<script src="/assets/theme.js" defer></script>
```

The first script must stay inline — it has to run before the stylesheet applies, otherwise the page flashes the wrong theme. The other two are external. Each template in `templates/` already includes this block; new pages copied from a template inherit it.

### Toggle placement

`theme.js` adapts placement to the page:

- **Slide pages**: detects `.header > .branding` (the "← Topics" back link) and appends the toggle inside `.header` as a flex sibling so it sits naturally in the header bar.
- **All other pages**: appends to `<body>` with `position: fixed; top: 16px; right: 16px;`.

### Tokens

```css
html[data-theme="light"] {
  --bg:  #f7f4ec;   /* warm paper background */
  --sf:  #ffffff;   /* white card surface */
  --sf2: #f1ebde;   /* hover surface */
  --bd:  #e3d8c5;   /* warm border */
  --bdh: #cbbb9d;   /* warm border hover */
  --tx:  #1c1f24;   /* primary text */
  --txM: #4d5969;   /* muted text */
  --txD: #7a8597;   /* dim text */
  --or:  #b36a0f;   /* darker orange for AA on light bg */
  --orB: #b36a0f;
  --orD: rgba(247,147,26,.12);
  --orG: rgba(247,147,26,.32);
}
```

The semantic accents (`--bl`, `--gn`, `--rd`, `--cy`, `--pu`, `--pk`, `--yl`, `--tl`) are **not** overridden — they read fine on warm paper and preserve the meaning each colour carries on topic cards.

### Backfill

To re-wire every page (e.g. after touching the templates), run:

```bash
python3 tools/wire_shared_theme.py
```

It is idempotent — already-wired pages report `skip`.

### Universal base in shared CSS

[`/assets/theme.css`](../assets/theme.css) also carries the three universals that every page needed inlined before:

- `* { margin:0; padding:0; box-sizing:border-box }`
- `body` base (background, color, font-family, min-height, font smoothing)
- `body::before` noise overlay (the 430-byte SVG data URI lives here once instead of in 33 inline copies)

Per-page inline `<style>` blocks may still extend `body` (slide pages add `display:flex; flex-direction:column; overflow-x:hidden`), and pages with bespoke palettes (e.g. `2026-03/cluster-mempool-example.html`) keep their own `body` and `body::before` declarations untouched. `:root` token defaults and `.glow` rules stay inline per page — palettes and glow accents vary too much across months and topics to share.

To re-run the base strip after touching `assets/theme.css`:

```bash
python3 tools/strip_canonical_base.py            # dry-run
python3 tools/strip_canonical_base.py --apply    # rewrite files
```

Like the chrome strip, it uses normalised exact-match comparison at the rule level for `*` and `body::before`, and property-level matching for `body` so slide pages keep their flex/overflow-x extras.

## Typography

### TV-friendly scale (May 2026 onward)

Pages are projected on a 4K TV via HDMI from a laptop. Font sizes were
scaled up (~1.4×) so text is legible from across the room. Use these
values for all new slide pages and hub pages:

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Hub h1 | JetBrains Mono | 800 | clamp(40px, 6vw, 60px) |
| Slide title (h2) | JetBrains Mono | 800 | 36px (mobile 30px) |
| Topic title in cards | JetBrains Mono | 700 | 22-24px |
| Body text / card-text | DM Sans | 400 | 20px |
| Subtitle | DM Sans | 400 | 20px |
| Box labels (info/warn/etc) | JetBrains Mono | 700 | 19px |
| Card-label, table cells | JetBrains Mono / DM Sans | 700/400 | 17-18px |
| Code (inline + blocks) | JetBrains Mono | 400 | 17px |
| Links in `.links` | JetBrains Mono | 400 | 19px |
| Nav buttons | JetBrains Mono | 400 | 17px |
| Nav-info, footer, badges | JetBrains Mono | 700 | 14-16px |
| Update tags | JetBrains Mono | 700 | 13px |

### Layout widths (TV-friendly)

| Element | Old | New (TV) |
|---------|-----|----------|
| Hub `.shell` max-width | 760px | **1080px** |
| Slide-inner max-width | 680-720px | **960px** |

Pre-May-2026 pages keep their original tighter sizing — do not retrofit.

The h1 on the landing page and month hubs uses a gradient fill:
```css
background: linear-gradient(135deg, #f7931a 0%, #fbbf24 50%, #f7931a 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

## Google Fonts Import

All pages use this import:
```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
```

## Shared Visual Elements

### Noise texture overlay (on body::before)
Subtle fractal noise at 2.5% opacity, `position:fixed`, `pointer-events:none`, `z-index:1000`.

### Orange glow (`.glow` div)
Radial gradient from `--orG` centered at top, blurred 80px, `opacity:.4`, `pointer-events:none`.

### Divider
```css
.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--bd) 30%, var(--bd) 70%, transparent 100%);
}
```

### Card left-accent border
All topic cards and event cards have a 3px left border accent (colored per category on slide pages, always orange on archive/landing pages):
```css
.topic::before {
  content: "";
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: var(--or);
  border-radius: 12px 0 0 12px;
  opacity: .6;
}
```

## Page Max Widths

| Page type | Max width |
|-----------|-----------|
| Landing page | 760px |
| Month hub (Feb 2026 – Apr 2026) | 760px |
| Month hub (May 2026 onward, TV-friendly) | **1080px** |
| Archive pages | 760px |
| Slide content area (Feb–Apr 2026) | 620-680px (varies per topic) |
| Slide content area (May 2026 onward, TV-friendly) | **960px** |
| Mining stack (wide layout) | 1100px |
| About page | 660px |

## Responsive Breakpoints

- `max-width: 600px` — slide pages collapse grids to single column
- `max-width: 480px` — reduce padding, shrink title fonts
