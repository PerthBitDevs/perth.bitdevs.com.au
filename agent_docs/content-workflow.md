# Content Workflow

## Contents

- [Monthly Content Pipeline](#monthly-content-pipeline)
- [Optional Newswatch + Issue Trigger](#optional-newswatch--issue-trigger)
- [Month Manifest](#month-manifest)
- [Prompt Pattern for Topic Creation](#prompt-pattern-for-topic-creation)
- [Multi-Agent Coordination](#multi-agent-coordination)
- [Archive Pages (Historical)](#archive-pages-historical)
- [File Naming](#file-naming)

## Monthly Content Pipeline

```
GitHub Issue                 Claude Code                 Website Repo
(PerthBitDevs/PerthBitDevs)  (research + creation)       (perth.bitdevs.com.au)
─────────────────────────    ─────────────────────       ──────────────────────
Community submits topic       Fetch issue, research,     Files created directly
comments on the monthly       create topic slide HTML    in repo, push to master
issue throughout the month    in the repo                → auto-deploys
```

### Step 1: Topic Collection

Topics are submitted as comments on the monthly GitHub issue (e.g. `PerthBitDevs/PerthBitDevs#32` for March 2026).

Each comment typically contains:
- A heading (h1/h2 or bold text) as the topic title
- Description or context
- Links to source material (PRs, papers, tweets, blog posts)
- Sometimes images

### Step 2: Fetch and Curate

Use Claude Code to pull the issue comments and assess the topics:

```bash
# Fetch the monthly issue and all comments
gh issue view <NUMBER> --repo PerthBitDevs/PerthBitDevs --comments
```

Editorial decisions at this stage:
- Which topics to cover in depth (slides) vs mention briefly on the hub page
- How to categorise and group topics (Technical/Protocol, Bitcoin Core, Mining, Privacy, etc.)
- What visual format suits each topic (linear slides, interactive expandable diagram, etc.)
- How many slides per topic (typically 2-5)

### Step 2.5: Optional Newswatch + Issue Trigger

Use the local newswatch helper when you want an AI-assisted scan of curated Bitcoin sources and the meetup GitHub issue since the last meetup or since the last scan:

```bash
just setup-newswatch
just news-scan since=YYYY-MM-DD issue=NN
just news-scan-preview since=YYYY-MM-DD issue=NN
```

After the first explicit-date run, `just news-scan` uses and advances the stored local cursor in `tools/newswatch/state.local.json`. Use `just news-scan-preview` to generate packet output without advancing that cursor. Add `issue=NN` to pull community topic comments from `PerthBitDevs/PerthBitDevs` into the same packet as the curated-source scan. Optional local import packets can be merged with scans:

```bash
just news-scan since=YYYY-MM-DD issue=NN import=tools/newswatch/imports/local.json
```

External packet schema documentation lives in `tools/newswatch/imports/README.md`. The helper writes Markdown and JSON planning packets under `tools/newswatch/runs/`; these files are ignored by git and should be treated as research inputs, not publishable content.

The packet is designed to be pasted into Codex or another LLM for topic triage. Ask the LLM to classify each item as:
- `dedicated deck`
- `news roundup`
- `watch`
- `ignore`

Then apply the existing editorial rules:
- Check the previous two months before re-covering a topic.
- Give GitHub issue submissions extra editorial weight, especially when they overlap with scanned-source clusters.
- Put short but interesting items into `news-roundup.html`.
- Use dedicated decks only for items that justify 3-5 slides.
- Verify claims before writing final HTML.

### Step 2.75: Update the Month Manifest

For current and upcoming meetups, create or update `YYYY-MM/manifest.json` before editing the month hub or landing page. The manifest is the monthly content interface for agents and local checks. Published pages still remain self-contained static HTML.

The manifest records:

- Event metadata: month, status, date, time, timezone, venue, and display labels.
- Source metadata: the monthly GitHub issue and any newswatch packet used for triage.
- Topic metadata: file, title, category, draft/final status, slide count, tags, source refs, and summary.
- Auxiliary page ownership: any month-local HTML page that is not a topic deck.
- Landing metadata: the month href and summary topics expected on `/index.html`.

The first tracked manifest is `2026-06/manifest.json`. Do not backfill historical manifests during ordinary content work unless a task explicitly asks for it.

### Step 3: Research and Create Topic Pages

For each selected topic, Claude Code:

1. **Researches** the source material (follows links, reads PRs, fetches relevant context)
2. **Creates** the topic slide HTML file at `YYYY-MM/topic-name.html`
3. **Follows** conventions in `slide-page-conventions.md` (keyboard nav, Esc handling, back link, scroll fix)
4. **Applies** the design system from `design-system.md` (color palette, typography, components)
5. **Respects** the voice rules in `voice-and-tone.md` and the size limits in `content-budget.md`

Each topic page is self-contained HTML with inline CSS and JS. Per-topic creative freedom within the shared design framework.

### Step 3.5: Mandatory Fact-Check Gate

**Before a topic deck is considered done**, run the `technical-accuracy-review` skill against it (in Codex: `$technical-accuracy-review path/to/topic.html`). This catches:

- Unverifiable numeric claims (May 2026 caught a Knots-node-count claim that was 4-10x off)
- Mis-attributed quotes (May 2026 caught a "stickies-v volunteered" attribution that was wrong)
- Stale dates and version numbers
- Internal inconsistencies between summary and detail slides

The review is review-only by default. Apply its proposed fixes deliberately, not blindly. If it flags `UNVERIFIABLE` claims, either find the source or remove the claim. Don't ship slides with unverified specifics.

### Step 4: Month Hub

Create `YYYY-MM/index.html` as a hub page linking to all topic pages. Use the Feb 2026 hub (`2026-02/index.html`) as the template:
- Cards grouped by category with color coding
- Each card links to the topic slide file
- Slide count or format type in card metadata
- "All Events" back link to landing page
- Footer linking to the source GitHub issue

Before considering the hub done, compare it against `YYYY-MM/manifest.json`: every topic file should be listed in the manifest and linked from the hub, and every non-topic HTML file should be listed under `auxiliary_pages`.

### Step 5: Landing Page Update

Update `/index.html`:
- Move the "Upcoming" section to point to the next month's issue
- Add the new month as the first entry under its year in "Past Events"
- Write a one-line description summarising the key topics covered

Use the manifest event metadata for the date, venue, topic count, and landing summary. This avoids drift between the homepage and month hub.

### Step 6: Deploy

Push to `master`. GitHub Pages serves the new content automatically.

Run `just site-check` before publishing. Run `just check` when the local newswatch environment is available.

## Prompt Pattern for Topic Creation

When creating a new month's content, a typical prompt flow:

1. "Fetch the comments from PerthBitDevs/PerthBitDevs issue #NN and list the topics"
2. "Create topic slide pages for these topics in YYYY-MM/"
3. "Run the technical-accuracy-review skill against each topic page and apply the high-severity fixes"
4. "Create the month hub page at YYYY-MM/index.html"
5. "Update the landing page with the new month"

## Multi-Agent Coordination

When using parallel research agents (a good fit for breadth), coordinate them to avoid the cross-file consistency bugs that May 2026 produced:

1. **Plan first, in one session**: produce a topic-to-file mapping and decide which deck owns each sub-thread before any research runs. Cross-references between decks are the agent contract.
2. **Parallel research only, not parallel drafting**: research agents return findings; a single drafting agent (or sequential drafting) writes HTML. Parallel HTML writers will diverge in voice and trample shared topics.
3. **One topic, one file**: never split a single topic across multiple HTML files. See the mega-topic rule in `content-budget.md`.
4. **After any rename, merge, or topic move**, grep all `YYYY-MM/*.html` for the old name and clean up stale references before declaring the work done.

## Archive Pages (Historical)

For months before the slide format was adopted (Dec 2023 - Dec 2025), archive pages were generated by pulling issue comments from GitHub and rendering them as a scrollable topic list. These are simpler than slide pages - no interactivity, just a well-formatted record.

## File Naming

| Item | Convention | Example |
|------|-----------|---------|
| Month directory | `YYYY-MM` | `2026-03` |
| Topic slide file | `kebab-case.html` | `cluster-mempool.html` |
| Month hub | `index.html` inside the month dir | `2026-03/index.html` |
