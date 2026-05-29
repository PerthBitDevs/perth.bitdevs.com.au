# Source Templates

These files are authoring templates for monthly content. They are not published
pages and they are not part of a build step.

Copy a template into the target month directory, replace every `{{PLACEHOLDER}}`,
then edit the copied page in place:

```bash
cp templates/manifest.json.tmpl 2026-07/manifest.json
cp templates/month-hub.html.tmpl 2026-07/index.html
cp templates/slide-deck.html.tmpl 2026-07/topic-name.html
```

Use the templates as the starting point for new pages instead of copying the
nearest previous month by eye. Published HTML should still be fully
self-contained with inline CSS and inline JavaScript.

## Template Map

- `manifest.json.tmpl` - current-month event metadata, topic list, source refs,
  auxiliary page ownership, and landing summary fields.
- `month-hub.html.tmpl` - TV-friendly current-month hub linking to topic pages.
- `slide-deck.html.tmpl` - canonical slide runtime, footer nav, Topics link, Esc
  handling, CSS tokens, TV scale, and accessible disclosure pattern.
- `auxiliary-visual-page.html.tmpl` - non-slide visual explainer with Topics
  link, Esc handling, and accessible step controls.
- `archive-page.html.tmpl` - historical scrollable topic archive page.

After copying:

1. Keep topic filenames in kebab-case.
2. Keep `target="_blank"` links paired with `rel="noopener"`.
3. List every current-month topic or auxiliary page in `manifest.json`.
4. Give each auxiliary page a `parent_topic` that matches a topic `file` entry.
5. Run `just site-check` or `just check`.
