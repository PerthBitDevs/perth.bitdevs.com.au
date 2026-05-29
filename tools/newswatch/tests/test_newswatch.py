from __future__ import annotations

import tempfile
import unittest
import warnings
from pathlib import Path

import httpx

from tools.newswatch import newswatch

warnings.filterwarnings("ignore", category=DeprecationWarning)


def source(**overrides):
    data = {
        "id": "sample",
        "title": "Sample Feed",
        "category": "protocol",
        "kind": "feed",
        "url": "https://example.com/feed.xml",
        "priority": "high",
        "tags": ["sample", "protocol"],
        "enabled": True,
    }
    data.update(overrides)
    return newswatch.Source(**data)


class NewswatchTests(unittest.TestCase):
    def test_canonicalize_url_removes_tracking_and_fragment(self):
        url = "https://Example.com:443/foo/?utm_source=x&b=2&a=1#section"
        self.assertEqual(newswatch.canonicalize_url(url), "https://example.com/foo?a=1&b=2")

    def test_parse_feed_candidates_filters_by_since(self):
        content = b"""<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>New proposal</title>
              <link>https://example.com/new?utm_medium=social</link>
              <guid>new-1</guid>
              <pubDate>Fri, 10 May 2026 10:00:00 GMT</pubDate>
              <description><![CDATA[<p>Fresh protocol discussion.</p>]]></description>
            </item>
            <item>
              <title>Old proposal</title>
              <link>https://example.com/old</link>
              <guid>old-1</guid>
              <pubDate>Fri, 01 May 2026 10:00:00 GMT</pubDate>
              <description>Old discussion.</description>
            </item>
          </channel>
        </rss>"""
        candidates, observed = newswatch.parse_feed_candidates(
            source(),
            content,
            since=newswatch.parse_date("2026-05-07"),
            seen_ids=set(),
            ignore_seen=False,
            limit=10,
        )
        self.assertEqual([item.title for item in candidates], ["New proposal"])
        self.assertEqual(len(observed), 2)
        self.assertEqual(candidates[0].canonical_url, "https://example.com/new")
        self.assertEqual(candidates[0].excerpt, "Fresh protocol discussion.")

    def test_parse_feed_candidates_skips_seen_items(self):
        content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>tag:example.com,2026:item</id>
            <title>Already seen</title>
            <link href="https://example.com/seen"/>
            <updated>2026-05-10T10:00:00Z</updated>
          </entry>
        </feed>"""
        first, observed = newswatch.parse_feed_candidates(
            source(),
            content,
            since=None,
            seen_ids=set(),
            ignore_seen=False,
            limit=10,
        )
        second, _ = newswatch.parse_feed_candidates(
            source(),
            content,
            since=None,
            seen_ids=set(observed),
            ignore_seen=False,
            limit=10,
        )
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    def test_extract_page_candidate_hashes_normalized_content(self):
        page_source = source(kind="page", url="https://example.com/page")
        html = """
        <html><head><title>Watch Page</title><meta name="description" content="Short summary"></head>
        <body><script>ignored()</script><main>Changed text</main></body></html>
        """
        candidate, content_hash = newswatch.extract_page_candidate(page_source, html)
        self.assertEqual(candidate.title, "Watch Page")
        self.assertEqual(candidate.excerpt, "Short summary")
        self.assertEqual(len(content_hash), 64)

    def test_dedupe_candidates_merges_canonical_urls(self):
        first = newswatch.Candidate(
            source_id="a",
            source_title="A",
            category="protocol",
            priority="high",
            tags=[],
            kind="feed",
            title="Shared item",
            url="https://example.com/item?utm_source=x",
            canonical_url=newswatch.canonicalize_url("https://example.com/item?utm_source=x"),
            raw_id="1",
            published_at=None,
            summary="",
            excerpt="",
        )
        second = newswatch.Candidate(
            source_id="b",
            source_title="B",
            category="protocol",
            priority="low",
            tags=[],
            kind="feed",
            title="Shared item",
            url="https://example.com/item",
            canonical_url=newswatch.canonicalize_url("https://example.com/item"),
            raw_id="2",
            published_at=None,
            summary="",
            excerpt="",
        )
        deduped = newswatch.dedupe_candidates([first, second])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].duplicate_sources, ["B"])

    def test_mark_recent_coverage_detects_existing_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            month = root / "2026-05"
            month.mkdir()
            (month / "topic.html").write_text(
                '<a href="https://example.com/item?utm_campaign=x">source</a>',
                encoding="utf-8",
            )
            candidate = newswatch.Candidate(
                source_id="a",
                source_title="A",
                category="protocol",
                priority="high",
                tags=["protocol"],
                kind="feed",
                title="Example Item",
                url="https://example.com/item",
                canonical_url=newswatch.canonicalize_url("https://example.com/item"),
                raw_id="1",
                published_at=None,
                summary="",
                excerpt="",
            )
            newswatch.mark_recent_coverage([candidate], root, 2)
            self.assertEqual(candidate.already_cited_paths, ["2026-05/topic.html"])

    def test_load_sources_validates_repo_config(self):
        sources = newswatch.load_sources(newswatch.DEFAULT_SOURCES_PATH)
        self.assertGreaterEqual(len(sources), 10)
        self.assertTrue(any(item.enabled for item in sources))

    def test_fetch_source_retries_without_conditional_headers_on_403(self):
        calls = []

        def handler(request):
            calls.append(dict(request.headers))
            if len(calls) == 1:
                self.assertIn("if-none-match", request.headers)
                return httpx.Response(403)
            self.assertNotIn("if-none-match", request.headers)
            return httpx.Response(200, text="ok")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        response = newswatch.fetch_source(
            client,
            source(url="https://example.com/feed.xml"),
            {"etag": '"abc"'},
            use_validators=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 2)

    def test_display_path_accepts_external_paths(self):
        self.assertEqual(newswatch.display_path(Path("/tmp/newswatch-test.md")), "/tmp/newswatch-test.md")

    def test_parse_github_issue_ref_accepts_common_forms(self):
        self.assertEqual(newswatch.parse_github_issue_ref("36", "PerthBitDevs/PerthBitDevs"), ("PerthBitDevs/PerthBitDevs", 36))
        self.assertEqual(
            newswatch.parse_github_issue_ref("owner/repo#7", "PerthBitDevs/PerthBitDevs"),
            ("owner/repo", 7),
        )
        self.assertEqual(
            newswatch.parse_github_issue_ref(
                "https://github.com/PerthBitDevs/PerthBitDevs/issues/36",
                "PerthBitDevs/PerthBitDevs",
            ),
            ("PerthBitDevs/PerthBitDevs", 36),
        )

    def test_github_issue_comment_becomes_candidate(self):
        comments = [
            {
                "id": "comment-1",
                "body": "## Sparrow wallet 2.5.0 released with initial Silent Payments support\n\nhttps://github.com/sparrowwallet/sparrow/releases/tag/2.5.0",
                "created_at": "2026-05-29T02:40:06Z",
                "updated_at": "2026-05-29T02:40:06Z",
                "url": "https://api.github.com/repos/PerthBitDevs/PerthBitDevs/issues/comments/1",
                "html_url": "https://github.com/PerthBitDevs/PerthBitDevs/issues/36#issuecomment-1",
                "user": {"login": "deadmanoz"},
                "isMinimized": False,
            }
        ]
        candidates = newswatch.github_issue_candidates_from_payload(
            "PerthBitDevs/PerthBitDevs",
            36,
            comments,
            since=newswatch.parse_date("2026-05-28"),
            limit=10,
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].title, "Sparrow wallet 2.5.0 released with initial Silent Payments support")
        self.assertEqual(candidates[0].url, "https://github.com/sparrowwallet/sparrow/releases/tag/2.5.0")
        self.assertEqual(candidates[0].published_at, "2026-05-29T02:40:06+00:00")
        self.assertIn("silent-payments", candidates[0].tags)
        self.assertIn("Submitted by @deadmanoz", candidates[0].excerpt)
        self.assertIn("GitHub comment: https://github.com/PerthBitDevs/PerthBitDevs/issues/36#issuecomment-1", candidates[0].excerpt)

    def test_github_issue_comment_filters_by_update_time(self):
        comments = [
            {
                "id": "comment-1",
                "body": "## Old topic",
                "createdAt": "2026-05-10T02:40:06Z",
                "updatedAt": "2026-05-10T02:40:06Z",
                "url": "https://github.com/PerthBitDevs/PerthBitDevs/issues/36#issuecomment-1",
                "author": {"login": "deadmanoz"},
                "isMinimized": False,
            }
        ]
        candidates = newswatch.github_issue_candidates_from_payload(
            "PerthBitDevs/PerthBitDevs",
            36,
            comments,
            since=newswatch.parse_date("2026-05-28"),
            limit=10,
        )
        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
