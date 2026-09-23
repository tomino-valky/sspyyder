"""
Pavúk — PubMed Spider

Scrapes research articles from PubMed using the NCBI E-utilities API.
Focused on neurobiology/neuroscience publications by default.

API Docs: https://www.ncbi.nlm.nih.gov/books/NBK25500/

HOW IT WORKS:
=============
PubMed doesn't allow HTML scraping — you MUST use their E-utilities API.
The workflow is a two-step process:

  1. SEARCH (esearch.fcgi):
     Send a search query → get back a list of PubMed IDs (PMIDs)

  2. FETCH (efetch.fcgi):
     Send a batch of PMIDs → get back full article records (XML)

This two-step pattern is called the "E-utilities pipeline" and is
how all PubMed programmatic access works.

IMPORTANT:
==========
  - Always include tool= and email= parameters (NCBI requirement)
  - Rate limit: 3 requests/sec without API key, 10/sec with one
  - Register for a free API key at: https://www.ncbi.nlm.nih.gov/account/

USAGE:
======
  # Default neurobiology search
  scrapy crawl pubmed

  # Custom search query
  scrapy crawl pubmed -a query="CRISPR AND brain"

  # Limit results
  scrapy crawl pubmed -a max_results=50

  # Specify how many days back to search
  scrapy crawl pubmed -a days=7

  # Use NCBI API key for higher rate limits
  scrapy crawl pubmed -a api_key="YOUR_KEY"
"""

from datetime import datetime, timedelta, timezone

import scrapy

from pavuk.items import PubMedArticle


class EquinePubMedSpider(scrapy.Spider):
    """Spider for PubMed via NCBI E-utilities (Equine focus).

    Spider Arguments:
        query: PubMed search query (default: equine terms)
        days: Number of days back to search (default: 7)
        max_results: Maximum number of articles to fetch (default: 100)
        email: Contact email for NCBI (required by their policy)
        api_key: NCBI API key for higher rate limits (optional)
    """

    name = "equine"
    allowed_domains = ["eutils.ncbi.nlm.nih.gov"]

    # Be extra polite to NCBI — they will block aggressive crawlers
    # NOTE: robots.txt is disabled because we're using the official
    # E-utilities API, not scraping HTML. NCBI requires API access
    # via E-utilities and will block HTML scrapers.
    custom_settings = {
        "DOWNLOAD_DELAY": 0.4,  # ~2.5 req/sec (under 3/sec limit)
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,
    }

    # ── API Configuration ──────────────────────────────────────────────
    ESEARCH_URL = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    )
    EFETCH_URL = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    )

    # Batch size for efetch requests (max 200 per NCBI docs)
    BATCH_SIZE = 50

    # Default equine/horse-focused search query
    DEFAULT_QUERY = '("horse"[Title/Abstract] OR "equine"[Title/Abstract])'

    def __init__(
        self,
        query=None,
        days=7,
        max_results=100,
        email="533883@mail.muni.cz",
        api_key=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.query = query or self.DEFAULT_QUERY
        self.days = int(days)
        self.max_results = int(max_results)
        self.email = email
        self.api_key = api_key

    # ── Entry Point ────────────────────────────────────────────────────

    async def start(self):
        """Step 1: Search PubMed for article IDs matching our query.

        Uses ``async def start()`` which is the entry point in Scrapy 2.13+
        (replaces the older ``start_requests()``).

        We add a date filter to only get recent articles (last N days).
        The 'reldate' parameter tells PubMed to only return articles
        published within the last N days.
        """
        params = {
            "db": "pubmed",
            "term": self.query,
            "retmode": "json",
            "retmax": self.max_results,
            "reldate": self.days,
            "datetype": "edat",  # Entrez date (when added to PubMed)
            "tool": "pavuk",
            "email": self.email,
            "sort": "date",  # Newest first
        }

        if self.api_key:
            params["api_key"] = self.api_key

        url = self._build_url(self.ESEARCH_URL, params)
        self.logger.info(
            f"Searching PubMed for: {self.query} (last {self.days} days)"
        )

        yield scrapy.Request(url=url, callback=self.parse_search_results)

    # ── Search Results Parsing ─────────────────────────────────────────

    def parse_search_results(self, response):
        """Parse the esearch JSON response to extract PMIDs.

        Response looks like:
        {
            "esearchresult": {
                "count": "1234",
                "idlist": ["38123456", "38123457", ...],
                ...
            }
        }

        Then we batch these IDs and send efetch requests.
        """
        data = response.json()
        result = data.get("esearchresult", {})
        id_list = result.get("idlist", [])
        total_count = result.get("count", "0")

        self.logger.info(
            f"PubMed search returned {total_count} total results, "
            f"fetching {len(id_list)} articles"
        )

        if not id_list:
            self.logger.warning("No articles found matching the query")
            return

        # Split IDs into batches and fetch full records for each batch
        for i in range(0, len(id_list), self.BATCH_SIZE):
            batch = id_list[i : i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            total_batches = (
                len(id_list) + self.BATCH_SIZE - 1
            ) // self.BATCH_SIZE

            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
                "rettype": "abstract",
                "tool": "pavuk",
                "email": self.email,
            }

            if self.api_key:
                params["api_key"] = self.api_key

            url = self._build_url(self.EFETCH_URL, params)

            self.logger.info(
                f"Fetching batch {batch_num}/{total_batches} "
                f"({len(batch)} articles)"
            )

            yield scrapy.Request(url=url, callback=self.parse_articles)

    # ── Article Parsing ────────────────────────────────────────────────

    def parse_articles(self, response):
        """Parse the efetch XML response to extract article details.

        The XML has this structure:
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>38123456</PMID>
              <Article>
                <ArticleTitle>...</ArticleTitle>
                <Abstract><AbstractText>...</AbstractText></Abstract>
                <Journal>...</Journal>
                <AuthorList>...</AuthorList>
              </Article>
              <MeshHeadingList>...</MeshHeadingList>
            </MedlineCitation>
            <PubmedData>
              <ArticleIdList>...</ArticleIdList>
            </PubmedData>
          </PubmedArticle>
          ...
        </PubmedArticleSet>

        We use Scrapy's built-in XPath selectors to navigate the XML.
        """
        # Scrapy's Selector works great with XML!
        articles = response.xpath("//PubmedArticle")

        for article in articles:
            item = self._parse_article(article)
            if item:
                yield item

    def _parse_article(self, article):
        """Extract fields from a single PubmedArticle XML element."""
        try:
            citation = article.xpath(".//MedlineCitation")

            # PMID
            pmid = citation.xpath(".//PMID/text()").get("")

            # Title
            # ArticleTitle may contain inline tags like <i>, <sub>, etc.
            title = citation.xpath(
                "string(.//Article/ArticleTitle)"
            ).get("")

            # Authors
            authors = []
            for author in citation.xpath(".//Author"):
                last = author.xpath("LastName/text()").get("")
                first = author.xpath("ForeName/text()").get("")
                if last:
                    authors.append(f"{last} {first}".strip())

            # Journal
            journal = citation.xpath(
                ".//Journal/Title/text()"
            ).get("")

            # Publication date — try multiple date formats
            pub_date = self._extract_pub_date(citation)

            # Abstract — may have multiple AbstractText elements
            # (structured abstracts with labels like "BACKGROUND",
            # "METHODS", etc.)
            abstract_parts = citation.xpath(
                ".//Abstract/AbstractText"
            )
            abstract = " ".join(
                part.xpath("string(.)").get("")
                for part in abstract_parts
            ).strip()

            # Keywords (MeSH terms)
            keywords = citation.xpath(
                ".//MeshHeading/DescriptorName/text()"
            ).getall()

            # DOI
            doi = article.xpath(
                './/ArticleId[@IdType="doi"]/text()'
            ).get("")

            return PubMedArticle(
                pmid=pmid,
                title=title,
                authors=authors,
                journal=journal,
                pub_date=pub_date,
                abstract=abstract,
                keywords=keywords,
                doi=doi,
                source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            )

        except Exception as e:
            self.logger.error(f"Error parsing article: {e}")
            return None

    def _extract_pub_date(self, citation):
        """Extract and normalize the publication date.

        PubMed dates can be in various formats. We try to produce
        a consistent YYYY-MM-DD string.
        """
        # Try ArticleDate first (electronic publication date)
        year = citation.xpath(
            ".//ArticleDate/Year/text()"
        ).get("")
        month = citation.xpath(
            ".//ArticleDate/Month/text()"
        ).get("")
        day = citation.xpath(
            ".//ArticleDate/Day/text()"
        ).get("")

        # Fall back to PubDate
        if not year:
            year = citation.xpath(
                ".//PubDate/Year/text()"
            ).get("")
            month = citation.xpath(
                ".//PubDate/Month/text()"
            ).get("")
            day = citation.xpath(
                ".//PubDate/Day/text()"
            ).get("")

        if year:
            month = month.zfill(2) if month.isdigit() else "01"
            day = day.zfill(2) if day and day.isdigit() else "01"
            return f"{year}-{month}-{day}"

        return ""

    def _build_url(self, base_url, params):
        """Build URL with query parameters."""
        from urllib.parse import urlencode
        return f"{base_url}?{urlencode(params)}"

