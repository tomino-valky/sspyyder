"""
Pavúk — bioRxiv / medRxiv Spider

Scrapes preprints from bioRxiv and medRxiv using their official REST API.
Focused on neuroscience preprints by default.

API Docs: https://api.biorxiv.org/

HOW IT WORKS:
=============
bioRxiv provides a simple REST API that returns preprint metadata
for a given date range:

  https://api.biorxiv.org/details/{server}/{start_date}/{end_date}/{cursor}/json

Each response contains up to 100 preprints and a total count for
pagination. We filter client-side by category (neuroscience, etc.)
since the API doesn't support server-side category filtering.

USAGE:
======
  # Default: neuroscience preprints from the last 7 days (bioRxiv)
  scrapy crawl biorxiv

  # Change time window
  scrapy crawl biorxiv -a days=14

  # Scrape medRxiv instead
  scrapy crawl biorxiv -a server=medrxiv

  # Scrape all categories (not just neuroscience)
  scrapy crawl biorxiv -a categories=all

  # Specific categories (comma-separated)
  scrapy crawl biorxiv -a categories="neuroscience,biophysics,genomics"
"""

from datetime import datetime, timedelta, timezone

import scrapy

from pavuk.items import BiorxivPreprint


class BiorxivSpider(scrapy.Spider):
    """Spider for bioRxiv / medRxiv preprint server API.

    Spider Arguments:
        server: "biorxiv" or "medrxiv" (default: biorxiv)
        days: How many days back to search (default: 7)
        categories: Comma-separated categories to include, or "all"
        max_pages: Maximum number of API pages to fetch (default: 20)
    """

    name = "biorxiv"
    allowed_domains = ["api.biorxiv.org"]

    # NOTE: robots.txt is disabled because we're using the official
    # bioRxiv REST API, not scraping HTML pages.
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,
    }

    # ── API Configuration ──────────────────────────────────────────────
    BASE_URL = "https://api.biorxiv.org/details"

    # Neuroscience-related categories on bioRxiv
    # Full list: https://www.biorxiv.org/subjects
    DEFAULT_CATEGORIES = {
        "neuroscience",
        "pharmacology and toxicology",
        "molecular biology",
        "cell biology",
        "bioinformatics",
        "genetics",
        "genomics",
        "biophysics",
        "biochemistry",
    }

    def __init__(
        self,
        server="biorxiv",
        days=7,
        categories=None,
        max_pages=20,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.server = server
        self.days = int(days)
        self.max_pages = int(max_pages)

        # Parse categories
        if categories is None:
            self.categories = self.DEFAULT_CATEGORIES
        elif categories.lower() == "all":
            self.categories = None  # None = accept all
        else:
            self.categories = {
                c.strip().lower() for c in categories.split(",")
            }

    # ── Entry Point ────────────────────────────────────────────────────

    async def start(self):
        """Generate the initial API request for the date range.

        Uses ``async def start()`` which is the entry point in Scrapy 2.13+
        (replaces the older ``start_requests()``).

        The bioRxiv API expects dates in YYYY-MM-DD format.
        We calculate the start date based on the 'days' argument.
        """
        now = datetime.now(timezone.utc)
        end_date = now.strftime("%Y-%m-%d")
        start_date = (now - timedelta(days=self.days)).strftime("%Y-%m-%d")

        self.logger.info(
            f"Searching {self.server} for preprints "
            f"from {start_date} to {end_date}"
        )

        if self.categories:
            self.logger.info(
                f"Filtering for categories: {', '.join(sorted(self.categories))}"
            )

        # cursor=0 means start from the first result
        url = (
            f"{self.BASE_URL}/{self.server}/"
            f"{start_date}/{end_date}/0/json"
        )

        yield scrapy.Request(
            url=url,
            callback=self.parse,
            cb_kwargs={"page": 1},
        )

    # ── Response Parsing ───────────────────────────────────────────────

    def parse(self, response, page):
        """Parse the API JSON response and yield BiorxivPreprint items.

        Response structure:
        {
            "messages": [{"status": "ok", "count": 100, "total": 5432}],
            "collection": [
                {
                    "doi": "10.1101/2026.08.15.123456",
                    "title": "...",
                    "authors": "Smith, J.; Doe, A.; ...",
                    "author_corresponding": "Smith, J.",
                    "category": "neuroscience",
                    "abstract": "...",
                    "date": "2026-08-15",
                    "published": "10.1038/s41586-026-12345-6",
                    ...
                },
                ...
            ]
        }
        """
        data = response.json()
        messages = data.get("messages", [{}])
        status = messages[0] if messages else {}
        total = status.get("total", 0)
        count = status.get("count", 0)

        collection = data.get("collection", [])

        self.logger.info(
            f"[{self.server}] Page {page}: received {len(collection)} "
            f"preprints (total available: {total})"
        )

        # Yield items, filtering by category
        yielded = 0
        skipped = 0
        for preprint in collection:
            category = preprint.get("category", "").lower()

            # Filter by category (if categories is None, accept all)
            if self.categories and category not in self.categories:
                skipped += 1
                continue

            item = self._parse_preprint(preprint)
            if item:
                yielded += 1
                yield item

        if skipped:
            self.logger.debug(
                f"Skipped {skipped} preprints outside target categories"
            )

        # ── Pagination ─────────────────────────────────────────────
        # The API returns 100 items per page. If we got 100, there
        # might be more. The cursor is the number of items to skip.
        if count >= 100 and page < self.max_pages:
            cursor = page * 100

            now = datetime.now(timezone.utc)
            end_date = now.strftime("%Y-%m-%d")
            start_date = (now - timedelta(days=self.days)).strftime(
                "%Y-%m-%d"
            )

            url = (
                f"{self.BASE_URL}/{self.server}/"
                f"{start_date}/{end_date}/{cursor}/json"
            )

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={"page": page + 1},
            )

    # ── Private Helpers ────────────────────────────────────────────────

    def _parse_preprint(self, preprint):
        """Extract fields from a single preprint JSON object."""
        try:
            doi = preprint.get("doi", "")
            published_doi = preprint.get("published", "")

            # "NA" means not yet published in a peer-reviewed journal
            if published_doi == "NA":
                published_doi = ""

            return BiorxivPreprint(
                doi=doi,
                title=preprint.get("title", ""),
                authors=preprint.get("authors", ""),
                category=preprint.get("category", ""),
                abstract=preprint.get("abstract", ""),
                pub_date=preprint.get("date", ""),
                server=self.server,
                published_doi=published_doi,
                source_url=f"https://www.biorxiv.org/content/{doi}",
            )

        except Exception as e:
            self.logger.error(f"Error parsing preprint: {e}")
            return None

