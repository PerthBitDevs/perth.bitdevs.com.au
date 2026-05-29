# Slide Page Conventions

Topic slide pages are the primary content format for monthly presentations (Feb 2026 onward). Each topic gets its own self-contained HTML file with slide-based navigation.

## Contents

- [HTML Structure](#html-structure)
- [Required Behaviours](#required-behaviours)
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

## Navigation JavaScript

Standard JS pattern used across all slide pages:

```javascript
const slides = document.querySelectorAll('.slide');
const names = Array.from(slides).map(s => s.dataset.name);
let cur = 0;
function render() {
  slides.forEach((s, i) => s.classList.toggle('active', i === cur));
  document.getElementById('dots').innerHTML = names.map((_, i) =>
    `<button class="dot${i === cur ? ' on' : ''}" onclick="goTo(${i})">${i + 1}</button>`
  ).join('');
  document.getElementById('navInfo').textContent = names[cur] + ' · ' + (cur + 1) + ' / ' + slides.length;
  document.getElementById('prevBtn').disabled = cur === 0;
  const nb = document.getElementById('nextBtn');
  nb.disabled = cur === slides.length - 1;
  nb.className = cur === slides.length - 1 ? 'nav-btn' : 'nav-btn next';
}
function go(d) { cur = Math.max(0, Math.min(slides.length - 1, cur + d)); render(); }
function goTo(i) { cur = i; render(); }
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') go(1);
  if (e.key === 'ArrowLeft') go(-1);
  if (e.key === 'Escape') window.location.href = '/YYYY-MM/';
});
render();
```

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

The common thread is the dark theme, color system, and navigation pattern. Content layout is free-form.

## When to Use Interactive Expandable Layouts

The mining stack MiningOS page (`2026-02/mining-stack-miningos.html`) is a strong reference for topics that benefit from **layered, expandable sections** rather than linear slides. Use this format when:

- The topic has a **hierarchical or stacked structure** (layers, levels, components)
- Users benefit from **seeing the whole picture first** then drilling into detail
- Content is better explored non-linearly (users may only care about certain layers)
- The topic involves **comparing multiple items at the same level** (e.g. firmware options, pool choices)

Key patterns from the MiningOS page:
- Collapsible layer cards with `onclick="this.classList.toggle('open')"`
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
