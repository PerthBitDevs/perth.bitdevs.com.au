# Design System

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
