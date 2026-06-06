# Content Budget

Perth BitDevs is a ~1–1.5 hour in-person meetup. Content must fit that envelope. Today's drafts overshoot routinely; this doc encodes the limits.

## Per-meetup target

| Dimension | Target | Hard cap |
|---|---|---|
| Total presentation time | 60–90 min | 100 min |
| Topic decks | 6–8 | 9 |
| Slides per deck | 3–5 | 7 |
| Total slides across all decks | ~30–40 | 50 |

If a draft exceeds the hard caps, **cut content first, not slides** — collapse adjacent slides, drop low-signal items, move minor items into the news roundup.

## Mega-topic rule

Some topics (quantum, BIP-110, governance) span multiple sub-threads in a given month. They get **one deck with multiple slides**, never multiple files.

- One `quantum-update.html` with 6–8 slides covering Project 11, hardware progress, SHRINCS/SHRIMPS, BIP-360, etc.
- Not three separate quantum HTML files (this happened in May 2026 from parallel agents and had to be consolidated).
- Use the slide structure inside the deck to compartmentalise sub-threads.

## News roundup is the catch-all

Items that don't justify a dedicated deck go into `news-roundup.html`. Use it actively — it's the pressure valve when a topic is interesting but not 4 slides' worth.

The roundup holds **only** items that do **not** get their own dedicated section. If a topic justifies its own section, it gets its own file (see the mega-topic rule above: one topic, one file, never a hash anchor inside `news-roundup.html`). The same item must never appear in both the quick-fire roundup and a dedicated deck. June 2026 shipped that duplication on first pass and had to unwind it. Think of the roundup as "things we're not going deep on." The hub's card arrangement (quick-fire card plus one card per dedicated section) is `content-workflow.md`'s lane; this doc owns only the routing decision of where each item lands.

Examples of news-roundup material from May 2026:
- INDOPACOM bitcoin node
- Iran toll-payment story
- Square Lightning expansion
- Litecoin reorg
- Vegas merger headline

Each becomes one news-roundup slide or one bullet on a multi-item slide. Not its own file.

Community-submitted items are real topics, not filler. A community item that is its own distinct topic gets its **own slide**; don't lump or dismiss it as "odds and ends", "misc", or "etc." (June 2026 made this mistake on first pass). Only genuinely minor items belong in the roundup; distinctness, not provenance, decides.

## Don't re-cover recent topics

Check the previous 2 months' decks before drafting. If a topic was covered in depth, don't re-litigate. A one-liner update under news roundup is fine; a fresh deep-dive isn't.

May 2026 examples that should have been caught earlier:
- Bitcoin Core v31 release — covered in detail in April; May only needed a one-liner
- ProductionReady client launch — covered in April; May only needed the post-launch criticism update
- BIP-110 mining-signal mechanics — covered repeatedly; May only needed the new developments

To check: `git diff $(cat agent_docs/.docs-ref)..HEAD -- '2026-*/*.html'` and skim the previous month's hub.

## When the budget is tight

Cut order, in priority:
1. Drop "history of this topic" recap slides — assume audience knows recent context
2. Collapse "voices for / voices against" into a single slide per topic
3. Move "what this signals" interpretation into one line at the bottom of the factual slide
4. Move minor items to news roundup
5. Drop the topic entirely; mention as a one-liner in the hub or news roundup

Cut order, never:
- Don't cut citations or sources to save space — bullet them tight, but keep them
- Don't cut neutrality balance — if you cut "for", cut "against" too

## Time-per-slide guidance

Rough budget for the presenter, useful when sizing content:
- Title/intro slide of a deck: 30–60s
- Standard content slide: 90–120s
- Dense data slide (table, multi-bullet): 2–3 min

Over-detailed slides cost speaking time the same way extra slides do. A slide stuffed with low-level implementation detail eats minutes whether or not the slide count looks fine, so when the budget is tight, **tighten dense slides, don't just count them**. June 2026 had decks carrying too much low-level detail and multi-sentence descriptions that one sentence would have covered. Lead with the result and why it matters; drop low-level detail unless that detail is the story.

A 5-slide deck is roughly 8–12 minutes of speaking time. Eight 5-slide decks is ~80 minutes — this is the upper bound.
