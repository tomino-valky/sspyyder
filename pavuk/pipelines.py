"""
Pavúk — Item Pipelines

Pipelines process every item after it's scraped, in order of priority
(lower number = runs first). Think of it as an assembly line:

    Spider yields item
        → TimestampPipeline (add metadata)
        → CleanTextPipeline (sanitize text)
        → DropIncompletePipeline (reject bad items)
        → DeduplicationPipeline (remove duplicates)
        → Feed Export (write to JSON)

Learn more: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
"""

import re
from datetime import datetime, timezone

from scrapy.exceptions import DropItem


class TimestampPipeline:
    """Adds scraping metadata to every item.

    Stamps each item with:
    - scraped_at: when the item was processed (UTC ISO timestamp)
    - spider_name: which spider produced this item

    This makes it easy to track when data was collected and from which source.

    Priority: 100 (runs first)
    """

    def process_item(self, item, spider):
        item["scraped_at"] = datetime.now(timezone.utc).isoformat()
        item["spider_name"] = spider.name
        return item


class CleanTextPipeline:
    """Cleans and normalizes text fields.

    Many APIs return text with:
    - HTML tags (e.g., <b>bold</b> in abstracts)
    - Excessive whitespace or newlines
    - Leading/trailing spaces

    This pipeline strips all of that to produce clean, readable text.

    Priority: 200
    """

    # Regex to match HTML tags like <p>, </b>, <br/>, etc.
    HTML_TAG_RE = re.compile(r"<[^>]+>")

    # Fields that should be cleaned (text fields across all item types)
    TEXT_FIELDS = {
        "title",
        "abstract",
        "summary",
        "official_title",
    }

    def process_item(self, item, spider):
        for field in self.TEXT_FIELDS:
            if field in item and isinstance(item[field], str):
                text = item[field]
                # Remove HTML tags
                text = self.HTML_TAG_RE.sub("", text)
                # Normalize whitespace (collapse multiple spaces/newlines)
                text = " ".join(text.split())
                # Strip leading/trailing whitespace
                text = text.strip()
                item[field] = text
        return item


class DropIncompletePipeline:
    """Drops items that are missing required fields.

    Every item MUST have a title and a unique identifier. Without these,
    the data is useless. This pipeline enforces that requirement.

    Priority: 300
    """

    # Map of item type → required fields
    REQUIRED_FIELDS = {
        "PubMedArticle": ["pmid", "title"],
        "ClinicalTrial": ["nct_id", "title"],
        "BiorxivPreprint": ["doi", "title"],
        "BiotechNews": ["title", "link"],
    }

    def process_item(self, item, spider):
        item_type = type(item).__name__
        required = self.REQUIRED_FIELDS.get(item_type, ["title"])

        for field in required:
            value = item.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                raise DropItem(
                    f"Missing required field '{field}' in {item_type}: "
                    f"{dict(item)}"
                )

        return item


class DeduplicationPipeline:
    """Prevents duplicate items within the same crawl session.

    Uses the item's unique identifier (PMID, NCT ID, DOI, or link URL)
    to track what we've already seen. If a duplicate appears, it's dropped.

    This is especially useful for API endpoints that may return overlapping
    results across paginated requests.

    Priority: 400 (runs last, after cleaning and validation)
    """

    def __init__(self):
        # Set of identifiers we've already seen in this crawl
        self.seen_ids = set()

    def process_item(self, item, spider):
        # Determine the unique identifier based on item type
        item_type = type(item).__name__

        if item_type == "PubMedArticle":
            unique_id = item.get("pmid")
        elif item_type == "ClinicalTrial":
            unique_id = item.get("nct_id")
        elif item_type == "BiorxivPreprint":
            unique_id = item.get("doi")
        elif item_type == "BiotechNews":
            unique_id = item.get("link")
        else:
            # Unknown item type — let it through
            return item

        if unique_id in self.seen_ids:
            raise DropItem(f"Duplicate {item_type}: {unique_id}")

        self.seen_ids.add(unique_id)
        return item

