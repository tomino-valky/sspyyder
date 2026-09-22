"""
Tests for Pavúk item definitions and pipeline logic.

Run with: python -m pytest tests/ -v
"""

import pytest

from pavuk.items import (
    BiotechNews,
    BiorxivPreprint,
    ClinicalTrial,
    PubMedArticle,
)
from pavuk.pipelines import (
    CleanTextPipeline,
    DeduplicationPipeline,
    DropIncompletePipeline,
    TimestampPipeline,
)


# ── Fake Spider for Testing ───────────────────────────────────────────


class FakeSpider:
    """Minimal spider mock for pipeline testing."""

    name = "test_spider"


# ── Item Creation Tests ───────────────────────────────────────────────


class TestItems:
    """Test that items can be created with expected fields."""

    def test_pubmed_article_fields(self):
        item = PubMedArticle(
            pmid="12345678",
            title="Neural plasticity in the hippocampus",
            authors=["Smith J", "Doe A"],
            journal="Nature Neuroscience",
            pub_date="2026-08-15",
            abstract="This study examines...",
            keywords=["Neuroplasticity", "Hippocampus"],
            doi="10.1038/s41593-026-01234-5",
            source_url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        )
        assert item["pmid"] == "12345678"
        assert item["journal"] == "Nature Neuroscience"
        assert len(item["authors"]) == 2

    def test_clinical_trial_fields(self):
        item = ClinicalTrial(
            nct_id="NCT05123456",
            title="A Study of Drug X in Alzheimer's Disease",
            status="RECRUITING",
            phase="PHASE2",
            conditions=["Alzheimer Disease"],
            interventions=[{"type": "DRUG", "name": "Drug X"}],
            sponsor="University Hospital",
        )
        assert item["nct_id"] == "NCT05123456"
        assert item["status"] == "RECRUITING"
        assert "Alzheimer Disease" in item["conditions"]

    def test_biorxiv_preprint_fields(self):
        item = BiorxivPreprint(
            doi="10.1101/2026.08.15.123456",
            title="Novel optogenetic approach",
            authors="Smith, J.; Doe, A.",
            category="neuroscience",
            server="biorxiv",
            pub_date="2026-08-15",
        )
        assert item["server"] == "biorxiv"
        assert item["category"] == "neuroscience"

    def test_biotech_news_fields(self):
        item = BiotechNews(
            title="New breakthrough in gene therapy",
            link="https://example.com/news/1",
            source_feed="FierceBiotech",
            published="2026-08-15T10:00:00+00:00",
        )
        assert item["source_feed"] == "FierceBiotech"


# ── Pipeline Tests ────────────────────────────────────────────────────


class TestTimestampPipeline:
    """Test the TimestampPipeline adds metadata."""

    def test_adds_scraped_at(self):
        pipeline = TimestampPipeline()
        spider = FakeSpider()
        item = PubMedArticle(pmid="123", title="Test")

        result = pipeline.process_item(item, spider)

        assert "scraped_at" in result
        assert result["spider_name"] == "test_spider"

    def test_scraped_at_is_iso_format(self):
        pipeline = TimestampPipeline()
        spider = FakeSpider()
        item = PubMedArticle(pmid="123", title="Test")

        result = pipeline.process_item(item, spider)

        # Should be parseable as ISO datetime
        from datetime import datetime

        datetime.fromisoformat(result["scraped_at"])


class TestCleanTextPipeline:
    """Test the CleanTextPipeline removes HTML and normalizes whitespace."""

    def test_removes_html_tags(self):
        pipeline = CleanTextPipeline()
        spider = FakeSpider()
        item = PubMedArticle(
            pmid="123",
            title="Gene <i>BRCA1</i> in <b>cancer</b>",
            abstract="<p>This study shows <b>significant</b> results.</p>",
        )

        result = pipeline.process_item(item, spider)

        assert result["title"] == "Gene BRCA1 in cancer"
        assert result["abstract"] == "This study shows significant results."

    def test_normalizes_whitespace(self):
        pipeline = CleanTextPipeline()
        spider = FakeSpider()
        item = PubMedArticle(
            pmid="123",
            title="  Too   many   spaces  ",
        )

        result = pipeline.process_item(item, spider)

        assert result["title"] == "Too many spaces"

    def test_leaves_non_text_fields_alone(self):
        pipeline = CleanTextPipeline()
        spider = FakeSpider()
        item = PubMedArticle(
            pmid="123",
            title="Test",
            authors=["Smith J"],
        )

        result = pipeline.process_item(item, spider)

        assert result["authors"] == ["Smith J"]


class TestDropIncompletePipeline:
    """Test the DropIncompletePipeline rejects items without required fields."""

    def test_passes_complete_item(self):
        pipeline = DropIncompletePipeline()
        spider = FakeSpider()
        item = PubMedArticle(pmid="123", title="Complete Article")

        result = pipeline.process_item(item, spider)
        assert result["pmid"] == "123"

    def test_drops_item_without_pmid(self):
        pipeline = DropIncompletePipeline()
        spider = FakeSpider()
        item = PubMedArticle(title="No PMID")

        from scrapy.exceptions import DropItem

        with pytest.raises(DropItem):
            pipeline.process_item(item, spider)

    def test_drops_item_without_title(self):
        pipeline = DropIncompletePipeline()
        spider = FakeSpider()
        item = PubMedArticle(pmid="123")

        from scrapy.exceptions import DropItem

        with pytest.raises(DropItem):
            pipeline.process_item(item, spider)

    def test_drops_clinical_trial_without_nct_id(self):
        pipeline = DropIncompletePipeline()
        spider = FakeSpider()
        item = ClinicalTrial(title="No NCT ID")

        from scrapy.exceptions import DropItem

        with pytest.raises(DropItem):
            pipeline.process_item(item, spider)


class TestDeduplicationPipeline:
    """Test the DeduplicationPipeline rejects duplicate items."""

    def test_allows_first_occurrence(self):
        pipeline = DeduplicationPipeline()
        spider = FakeSpider()
        item = PubMedArticle(pmid="123", title="First")

        result = pipeline.process_item(item, spider)
        assert result["pmid"] == "123"

    def test_drops_duplicate(self):
        pipeline = DeduplicationPipeline()
        spider = FakeSpider()

        item1 = PubMedArticle(pmid="123", title="First")
        item2 = PubMedArticle(pmid="123", title="Duplicate")

        pipeline.process_item(item1, spider)

        from scrapy.exceptions import DropItem

        with pytest.raises(DropItem):
            pipeline.process_item(item2, spider)

    def test_allows_different_ids(self):
        pipeline = DeduplicationPipeline()
        spider = FakeSpider()

        item1 = PubMedArticle(pmid="123", title="First")
        item2 = PubMedArticle(pmid="456", title="Second")

        pipeline.process_item(item1, spider)
        result = pipeline.process_item(item2, spider)
        assert result["pmid"] == "456"

    def test_deduplicates_across_item_types(self):
        """Each item type has its own ID field — no cross-type collision."""
        pipeline = DeduplicationPipeline()
        spider = FakeSpider()

        article = PubMedArticle(pmid="123", title="Article")
        trial = ClinicalTrial(nct_id="NCT123", title="Trial")

        pipeline.process_item(article, spider)
        result = pipeline.process_item(trial, spider)
        assert result["nct_id"] == "NCT123"

