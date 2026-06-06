# Voice and Tone

The single biggest source of churn in monthly content production is voice. Per-topic creative latitude lives in **layout** (slide structure, components, colour) — **not** in voice. Voice is shared and consistent across every deck.

## Contents

- [Register](#register)
- [Banned phrases and patterns](#banned-phrases-and-patterns)
- [Plain-English-first](#plain-english-first)
- [Right-size the detail](#right-size-the-detail)
- [Bullets vs prose](#bullets-vs-prose)
- [Headings](#headings)
- [Quoting and attribution](#quoting-and-attribution)
- [Self-check before submitting a deck](#self-check-before-submitting-a-deck)

## Register

Concise, factual, neutral. Present what happened and what was said. Let the audience decide.

- Pure facts of the matter — dates, links, names, numbers.
- No editorialising, no scene-setting, no slogans.
- No "biggest", "first ever", "near-disaster", "most ... of the year" unless objectively true and cited.
- Be especially careful with neutrality on contested topics (BIP-110, governance threads, alt-clients, eCash). Present opposition and support side by side; don't pick winners. If an item is contested, its criticism is part of the content; leaving it out is neutrality by omission, not balance (June 2026 first pass dropped the Kagikai criticism).

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
- `odds and ends` / `odd-ends` / `misc` / `etc.` lumping of community-submitted topics. Each distinct community item is a real topic and gets its own slide; never bundle or dismiss them

### Slide-meta filler
- `in-window`, `in window`, `the window`, `Apr 7 → May 7, 2026 — five threads ran in parallel and rarely cross-quoted each other` — readers know the window implicitly
- `a 10-slide neutral overview` — describing the deck inside the deck
- `the biggest financial story out of [event] — and it isn't a price chart` — TV-news style framing
- `Workshops, socialising, networking` — generic event filler
- `RECORDINGS WORTH CATCHING` / `talks worth scrubbing` — colloquial section titles
- `first pass` / `First Pass` (badge or text), `Newswatch found`, `DRAFT TAKEAWAY`, `WATCH ITEM`, `NEEDS REVIEW`, `EDITORIAL RULE`, `What To Split Out`, internal source lists, `read before presenting`, `needs source review`: planning and editorial meta from the local newswatch packet. The packet is research input only (`content-workflow.md` already flags `runs/` packets as "not publishable content"); its classification labels and scaffolding must never reach published HTML. Participants don't need to know how the deck was assembled.

### Cross-topic stale references
After a topic merge or rename, sweep every other deck. May 2026 had `ProductionReady` references in `governance.html` and `alt-clients.html` long after the topic was consolidated. **After any rename/merge, grep all `2026-MM/*.html` for the old name.**

## Plain-English-first

The audience is a **smart layperson who knows Bitcoin basics, not a Core developer**. Don't open a slide with jargon or the math. Lead with a plain-English framing or analogy, **then** name the concept, **then** show the specifics or the math. When a quantity is unfamiliar, add a scale-anchor number so a layperson can compare.

This is the same target as Right-size the detail (below), seen from the opposite side: aim for neither a thin slide nor a wall of jargon.

### Plain-English-first before/after

**Before** (QCAP, jargon-first):
> QCAP places a canary on a weaker elliptic curve to detect an ECDLP break before the secp256k1 chain is affected.

**After** (plain framing, then concept, then specifics):
> QCAP is a canary in a coal mine. It funds a Bitcoin key whose secret also lives on a smaller, weaker curve (NIST secp192r1), so that curve breaks first: smaller curve = easier to attack = tripped before the main chain. If anyone sweeps the canary, the on-chain spend is the alarm.

**Before** (OP_TWEAKADD / BIP-449, math-first):
> OP_TWEAKADD computes Q = P + t·G, committing the tweak t to the internal key P.

**After** (plain framing, then named step, then math):
> When you build a Taproot address, your wallet quietly combines a public key with extra commitments. That combine step is called a "tweak". Only then show the math: Q = P + t·G.

Scale-anchor examples (add a comparison number when the quantity is unfamiliar):
- Lattices: open with "high-dimensional grids whose hard problems don't collapse under any known quantum algorithm" before naming "NIST finalists"; note these signatures are much bigger than Schnorr's 64-byte sigs.
- P2WOTS: a Schnorr Taproot key-path spend is ~57.5 vbytes versus ~434 vbytes for P2WOTS, nearly 8x larger.

## Right-size the detail

Lead with the result and why it matters. Roll secondary numbers into prose. Cut low-level implementation detail **unless that detail is the story**. Right-size for neither thin nor jargon-wall (the same target as Plain-English-first, above, seen from the other side).

### Right-size before/after

**Before** (over-detail, three sentences of implementation trivia):
> The visible adoption signal sits with Sparrow: Craig Raw's sparrowwallet org maintains duckdb-ufsecp-extension, a DuckDB extension that uses libufsecp for BIP-352 Silent Payments scanning with optional CUDA, OpenCL, and Apple Metal GPU paths. Not in the Sparrow desktop binary itself, in the silent-payments tooling around it.

**After** (result first, secondary detail rolled into prose):
> The adoption signal is a Craig Raw DuckDB extension that GPU-accelerates BIP-352 Silent Payments scanning: tooling around Sparrow, not the desktop wallet itself.

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
- Every slide leads with the result / why-it-matters, not jargon or math (see Plain-English-first and Right-size the detail above)
- Run a banned-token grep across all month files before declaring done:
  ```sh
  grep -rinE 'first pass|newswatch found|draft takeaway|watch item|needs review|editorial rule|what to split out|read before presenting|needs source review|in[- ]window|the window|odds and ends|odd-ends' 2026-*/*.html
  ```
  (Adjust the month glob to the month you're shipping.) Expect zero hits before you ship. This makes the existing `in window` / `the window` ban above actually enforceable, not just listed.
