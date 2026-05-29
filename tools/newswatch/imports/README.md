# Newswatch External Import Packets

`newswatch scan` can merge local candidate packets created by tools outside this
repo:

```bash
just news-scan since=2026-05-07 issue=36 import=tools/newswatch/imports/example.json
```

Packets are JSON files with this top-level shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-05-29T04:00:00Z",
  "source": {
    "id": "local-export",
    "title": "Local Export",
    "category": "protocol",
    "priority": "medium",
    "tags": ["local"]
  },
  "candidates": [
    {
      "id": "stable-source-item-id",
      "title": "Candidate title",
      "url": "https://example.com/source",
      "published_at": "2026-05-29T02:00:00Z",
      "updated_at": "2026-05-29T02:30:00Z",
      "summary": "Short neutral summary.",
      "tags": ["wallet"],
      "provenance": {
        "reference_url": "external://record/stable-source-item-id",
        "source_url": "https://example.com/source",
        "original_location": "Local export collection"
      }
    }
  ]
}
```

## Required Fields

- `schema_version`: must be `1`.
- `candidates`: array of candidate objects.
- Candidate `title`: non-empty string.

## Optional Defaults

Use top-level `source` or `defaults` to avoid repeating metadata. Candidate
fields override defaults.

- `id` or `source_id`: stable source identifier.
- `title` or `source_title`: human-readable source name.
- `category`: packet category. Defaults to `external`.
- `priority`: `high`, `medium`, or `low`. Defaults to `medium`.
- `tags`: array of strings merged into every candidate.
- `kind`: candidate kind. Defaults to `external_import`.

## Candidate Fields

- `id` or `raw_id`: stable item identifier. If omitted, newswatch hashes the
  packet path and candidate content.
- `title`: required display title.
- `url` or `link`: primary source URL. If omitted, `provenance.reference_url` is
  used. If no URL is available, newswatch creates an internal
  `external-candidate://` URL for dedupe.
- `canonical_url`: optional explicit dedupe key. Otherwise newswatch canonicalizes
  `url`.
- `published_at`, `created_at`, `updated_at`: ISO-like timestamps. `--since`
  filters on `updated_at`, then `published_at`.
- `summary` or `excerpt`: short text shown in the Markdown packet.
- `tags`: array of strings merged with default tags.
- `provenance`: object with stable metadata needed to identify the original item.
  Suggested keys are `reference_url`, `source_url`, `email_subject`,
  `record_uuid`, `month_group`, `creation_date`, and `original_location`.

Import packets are local planning artefacts. Do not commit packets containing
private or machine-specific content.
