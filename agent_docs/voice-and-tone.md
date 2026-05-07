# Voice and Tone

The single biggest source of churn in monthly content production is voice. Per-topic creative latitude lives in **layout** (slide structure, components, colour) — **not** in voice. Voice is shared and consistent across every deck.

## Register

Concise, factual, neutral. Present what happened and what was said. Let the audience decide.

- Pure facts of the matter — dates, links, names, numbers.
- No editorialising, no scene-setting, no slogans.
- No "biggest", "first ever", "near-disaster", "most ... of the year" unless objectively true and cited.
- Be especially careful with neutrality on contested topics (BIP-110, governance threads, alt-clients, eCash). Present opposition and support side by side; don't pick winners.

## Banned phrases and patterns

These recurred across May 2026 and required multi-pass cleanup. Don't write them.

### Slang and meme phrases
- `Luke ratio'd` / `got Luke-ratio'd`
- `tea leaves` / `reading the tea leaves`
- `stalking-horses`
- `altcoin with extra steps`
- `iatrogenic` (or any medical metaphor)
- `sucks oxygen from`
- `fresh off the press`
- `flipping a switch`
- `paper over`
- `weaponise`
- `DUMPS QUIETLY` (or any all-caps verb-as-headline)

### Editorial framing
- `the spam war` → `data-carrier debate`
- `ticking bomb` → `future risk`
- `near-disaster bug` → `serious bug`
- `the politics` → `social coordination`
- `purportedly meritocratic` / loaded adverbs — drop the adverb, attribute the claim
- `"everything's fine" or "everything's stuck"` (false-binary framings)

### Slide-meta filler
- `in-window`, `in window`, `the window`, `Apr 7 → May 7, 2026 — five threads ran in parallel and rarely cross-quoted each other` — readers know the window implicitly
- `a 10-slide neutral overview` — describing the deck inside the deck
- `the biggest financial story out of [event] — and it isn't a price chart` — TV-news style framing
- `Workshops, socialising, networking` — generic event filler
- `RECORDINGS WORTH CATCHING` / `talks worth scrubbing` — colloquial section titles

### Cross-topic stale references
After a topic merge or rename, sweep every other deck. May 2026 had `ProductionReady` references in `governance.html` and `alt-clients.html` long after the topic was consolidated. **After any rename/merge, grep all `2026-MM/*.html` for the old name.**

## Bullets vs prose

**Default to bullets** for any block of dense factual content. Prose is acceptable for one-paragraph framing or attributed quotes; not for stat lists, dates, attribution sets, or "what happened".

### Canonical before/after

**Before** (wall of text — caused multiple rewrite rounds in May):
> Bitcoin Core v31.0 was published on bitcoincore.org 2026-04-19, GitHub release 2026-04-20, and announced on bitcoindev 2026-04-22 (Ava Chow). No add/remove activity to the maintainer set since April; the most recent change was TheCharlatan added 2026-01-08. Current set (six): Michael Ford (fanquake) · Ava Chow · Hennadii Stepanov (hebasto) · Ryan Ofsky · TheCharlatan · glozow.

**After** (bullets):
> **v31.0 release**
> - 2026-04-19 — published on bitcoincore.org
> - 2026-04-20 — GitHub release
> - 2026-04-22 — announced on bitcoindev (Ava Chow)
>
> **Maintainer set (6, unchanged since 2026-01-08)**
> - Michael Ford (fanquake)
> - Ava Chow
> - Hennadii Stepanov (hebasto)
> - Ryan Ofsky
> - TheCharlatan
> - glozow

### When prose works
- One-paragraph context-setting at the top of a slide
- A direct quote with attribution
- A "what this signals" interpretation paragraph (one only, and only if needed)

## Headings

Slide titles should describe content, not perform. Avoid slogans, alliteration for its own sake, and rhetorical questions used as titles.

- ❌ `Ocean Climbs — Signaling Doesn't Follow`
- ✅ `Ocean Hashrate Rose; BIP-110 Signaling Did Not`
- ❌ `Where The Conversation Was — & Read`
- ✅ `Where the Conversation Happened`
- ❌ `Reading the Tea Leaves`
- ✅ `What This Signals`
- ❌ `Song's Promo & the "Luke Ratio"`
- ✅ `ProductionReady Launch & Early Criticism`

## Quoting and attribution

- Quotes must be attributable to a named person, post, or recording. If you can't find the source, don't quote it.
- Don't paraphrase a quote unless flagged as a paraphrase.
- For supportive/opposition framings, name the speaker per quote (don't lump "supporters say X").
- Avoid attributing positions a person didn't take. May 2026 had `stickies-v volunteered` for a position that wasn't a volunteering — verify before attributing.

## Self-check before submitting a deck

Run through this list before declaring a deck done:

- No phrase from the banned list above appears
- Every dense factual block uses bullets
- Every contested claim has a named source or is removed
- After any merge/rename, grep across all month files for stale references
- Headings describe content, not opinion
