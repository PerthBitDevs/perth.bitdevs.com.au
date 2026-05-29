# Perth BitDevs

Website for [Perth BitDevs](https://perth.bitdevs.com.au), a monthly socratic seminar exploring Bitcoin development and the broader technical ecosystem.

Pure static HTML hosted on GitHub Pages. No build step, no frameworks.

## Structure

- `index.html` - Landing page with event listings
- `about.html` - About, rules, and privacy info
- `YYYY-MM/index.html` - Monthly hub pages linking to topic slides
- `YYYY-MM/manifest.json` - Current-month source of truth for event and topic metadata
- `YYYY-MM/topic-name.html` - Individual topic slide pages

## Monthly Manifests

For current and upcoming meetups, update `YYYY-MM/manifest.json` before changing the month hub or landing page. The manifest records the event date, venue, issue link, topic files, status, summaries, and auxiliary page ownership. Published pages remain plain static HTML.

## Contributing Topics

Submit discussion topics on the [GitHub issues](https://github.com/PerthBitDevs/PerthBitDevs/issues).

## Newswatch Helper

The repo includes a local Python helper for collecting candidate Bitcoin news from curated sources before each meetup.

```bash
just setup-newswatch
just news-scan since=2026-05-07 issue=36
```

The scan writes an LLM-ready Markdown packet and matching JSON under `tools/newswatch/runs/`. Add `issue=NN` to include community topic comments from `PerthBitDevs/PerthBitDevs` in the same packet as the curated-source scan. These files are local planning artefacts and are ignored by git. Source configuration lives in `tools/newswatch/sources.json`.

## Checks

```bash
just site-check
just check
```

`just site-check` validates local static-site contracts without network access. `just check` runs the site checker plus the local newswatch validation and tests.
