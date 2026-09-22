"""
Pavúk — RSS Feed Spider

Aggregates biotechnology and neuroscience news from RSS/Atom feeds.
Uses the feedparser library for robust feed parsing.

HOW IT WORKS:
=============
RSS (Really Simple Syndication) is a standardized XML format that
websites use to publish updates. Most scientific journals and news
sites provide RSS feeds. This spider:

  1. Fetches each RSS feed URL
  2. Parses the XML with feedparser
  3. Filters entries by publication date (last N days)
  4. Yields BiotechNews items

USAGE:
======
  # Run with all default feeds
  scrapy crawl rss

  # Only fetch entries from the last 3 days
  scrapy crawl rss -a days=3

  # Add a custom feed URL
  scrapy crawl rss -a extra_feed="https://example.com/feed.xml"
"""

from datetime import datetime, timedelta, timezone

import scrapy

try:
    import feedparser
except ImportError:
    feedparser = None

from pavuk.items import BiotechNews


class RssSpider(scrapy.Spider):
    """Spider that aggregates biotech news from RSS feeds.

    Spider Arguments:
        days: How many days back to include entries (default: 7)
        extra_feed: Additional RSS feed URL to include
    """

    name = "rss"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    # ── Feed Configuration ─────────────────────────────────────────────
    # Each feed is a dict with 'name', 'url', and 'category'.
    # You can add or remove feeds here!
    FEEDS_LIST = [
        {
            "name": "Nature Biotechnology",
            "url": "https://www.nature.com/subjects/biotechnology.rss",
            "category": "research",
        },
        {
            "name": "Nature Neuroscience",
            "url": "https://www.nature.com/neuro.rss",
            "category": "research",
        },
        {
            "name": "FierceBiotech",
            "url": "https://www.fiercebiotech.com/rss/xml",
            "category": "industry",
        },
        {
            "name": "BMC Neuroscience",
            "url": "https://bmcneurosci.biomedcentral.com/articles/most-recent/rss.xml",
            "category": "research",
        },
        {
            "name": "Neuroscience News",
            "url": "https://neurosciencenews.com/feed/",
            "category": "news",
        },
    ]

    def __init__(self, days=7, extra_feed=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.days = int(days)

        # Allow adding a custom feed via spider argument
        self.feeds = list(self.FEEDS_LIST)
        if extra_feed:
            self.feeds.append(
                {
                    "name": "Custom Feed",
                    "url": extra_feed,
                    "category": "custom",
                }
            )

    # ── Entry Point ────────────────────────────────────────────────────

    async def start(self):
        """Generate one request per RSS feed.

        Uses ``async def start()`` which is the entry point in Scrapy 2.13+
        (replaces the older ``start_requests()``).
        """
        if feedparser is None:
            self.logger.error(
                "feedparser is not installed! "
                "Run: pip install feedparser"
            )
            return

        for feed_info in self.feeds:
            self.logger.info(
                f"Fetching RSS feed: {feed_info['name']} "
                f"({feed_info['url']})"
            )
            yield scrapy.Request(
                url=feed_info["url"],
                callback=self.parse_feed,
                cb_kwargs={"feed_info": feed_info},
                # Some feeds don't set proper content-type
                headers={"Accept": "application/rss+xml, application/xml, text/xml"},
            )

    # ── Feed Parsing ───────────────────────────────────────────────────

    def parse_feed(self, response, feed_info):
        """Parse an RSS feed response using feedparser.

        feedparser handles all the quirks of different RSS/Atom formats,
        date parsing, encoding, and malformed feeds. It's the standard
        Python library for this job.
        """
        feed = feedparser.parse(response.text)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days)

        entries_count = 0
        skipped_old = 0

        for entry in feed.entries:
            # Parse the entry's publication date
            pub_date = self._parse_date(entry)

            # Skip entries older than our cutoff
            if pub_date and pub_date < cutoff_date:
                skipped_old += 1
                continue

            # Format date as ISO string
            pub_date_str = pub_date.isoformat() if pub_date else ""

            # Extract summary/description
            summary = entry.get("summary", "") or entry.get(
                "description", ""
            )

            # Extract category/tags
            categories = [
                tag.get("term", "")
                for tag in entry.get("tags", [])
                if tag.get("term")
            ]
            category = ", ".join(categories) if categories else feed_info.get(
                "category", ""
            )

            entries_count += 1
            yield BiotechNews(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                summary=summary,
                published=pub_date_str,
                source_feed=feed_info["name"],
                feed_url=feed_info["url"],
                category=category,
            )

        self.logger.info(
            f"[{feed_info['name']}] Yielded {entries_count} entries, "
            f"skipped {skipped_old} old entries"
        )

    # ── Private Helpers ────────────────────────────────────────────────

    def _parse_date(self, entry):
        """Extract and parse the publication date from a feed entry.

        feedparser normalizes dates into a 'published_parsed' or
        'updated_parsed' struct_time. We convert to a timezone-aware
        datetime.
        """
        import time
        import calendar

        # Try published_parsed first, then updated_parsed
        time_struct = entry.get("published_parsed") or entry.get(
            "updated_parsed"
        )

        if time_struct:
            try:
                timestamp = calendar.timegm(time_struct)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except (ValueError, OverflowError):
                pass

        # Fallback: try to parse the raw date string
        raw_date = entry.get("published") or entry.get("updated")
        if raw_date:
            try:
                from dateutil import parser as dateutil_parser

                return dateutil_parser.parse(raw_date).astimezone(
                    timezone.utc
                )
            except (ValueError, ImportError):
                pass

        return None

