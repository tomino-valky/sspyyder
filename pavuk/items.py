"""
Pavúk — Data Models (Scrapy Items)

Defines the structured data schemas for all four spiders.
Each item represents one record from a specific data source.

Scrapy Items work like dictionaries but with a defined schema,
which helps catch typos and ensures consistent field names across
spiders and pipelines.

Learn more: https://docs.scrapy.org/en/latest/topics/items.html
"""

import scrapy


class PubMedArticle(scrapy.Item):
    """A research article from PubMed (NCBI E-utilities).

    PubMed is the largest biomedical literature database, maintained by the
    US National Library of Medicine. Each article is identified by a unique
    PMID (PubMed ID).
    """

    # Unique identifier
    pmid = scrapy.Field()  # e.g. "38123456"

    # Bibliographic metadata
    title = scrapy.Field()
    authors = scrapy.Field()  # List of author names
    journal = scrapy.Field()  # Journal title
    pub_date = scrapy.Field()  # Publication date (ISO format string)
    doi = scrapy.Field()  # Digital Object Identifier, if available

    # Content
    abstract = scrapy.Field()  # Full abstract text
    keywords = scrapy.Field()  # List of MeSH terms / keywords

    # Traceability
    source_url = scrapy.Field()  # URL to the PubMed page
    scraped_at = scrapy.Field()  # Timestamp when this item was scraped
    spider_name = scrapy.Field()  # Name of the spider that produced this item


class ClinicalTrial(scrapy.Item):
    """A clinical trial from ClinicalTrials.gov (API v2).

    ClinicalTrials.gov is a database of privately and publicly funded
    clinical studies. Each trial has a unique NCT ID (National Clinical
    Trial Identifier), e.g. "NCT05123456".

    This is particularly relevant for neurobiology research — tracking
    trials for neurological conditions like Alzheimer's, Parkinson's,
    ALS, multiple sclerosis, epilepsy, and brain tumors.
    """

    # Unique identifier
    nct_id = scrapy.Field()  # e.g. "NCT05123456"

    # Study metadata
    title = scrapy.Field()  # Brief title of the study
    official_title = scrapy.Field()  # Full official title
    status = scrapy.Field()  # e.g. "RECRUITING", "COMPLETED"
    phase = scrapy.Field()  # e.g. "PHASE1", "PHASE2", "PHASE3"
    study_type = scrapy.Field()  # e.g. "INTERVENTIONAL", "OBSERVATIONAL"

    # Clinical details
    conditions = scrapy.Field()  # List of conditions studied
    interventions = scrapy.Field()  # List of dicts: {type, name, description}
    primary_outcomes = scrapy.Field()  # List of primary outcome measures
    enrollment = scrapy.Field()  # Number of participants (planned or actual)

    # Organization
    sponsor = scrapy.Field()  # Lead sponsor name
    collaborators = scrapy.Field()  # List of collaborator names

    # Dates
    start_date = scrapy.Field()  # Study start date
    completion_date = scrapy.Field()  # Estimated or actual completion date
    last_updated = scrapy.Field()  # Last time the record was updated

    # Description
    summary = scrapy.Field()  # Brief summary of the study

    # Traceability
    source_url = scrapy.Field()
    scraped_at = scrapy.Field()
    spider_name = scrapy.Field()


class BiorxivPreprint(scrapy.Item):
    """A preprint from bioRxiv or medRxiv.

    Preprints are research manuscripts posted before peer review.
    bioRxiv covers biology, medRxiv covers health sciences.
    Preprints in neuroscience often appear here weeks or months
    before journal publication.
    """

    # Unique identifier
    doi = scrapy.Field()  # e.g. "10.1101/2026.08.15.123456"

    # Metadata
    title = scrapy.Field()
    authors = scrapy.Field()  # Semicolon-separated author string from API
    category = scrapy.Field()  # e.g. "neuroscience", "bioinformatics"
    server = scrapy.Field()  # "biorxiv" or "medrxiv"

    # Content
    abstract = scrapy.Field()

    # Dates
    pub_date = scrapy.Field()  # Date posted on the preprint server

    # Publication status
    published_doi = scrapy.Field()  # DOI of the peer-reviewed version, if any

    # Traceability
    source_url = scrapy.Field()
    scraped_at = scrapy.Field()
    spider_name = scrapy.Field()


class BiotechNews(scrapy.Item):
    """A news item from a biotechnology RSS feed.

    Aggregates headlines from sources like Nature Biotechnology,
    FierceBiotech, and BMC Biotechnology to keep up with industry
    trends and breakthroughs.
    """

    # Content
    title = scrapy.Field()
    link = scrapy.Field()  # URL to the full article
    summary = scrapy.Field()  # Short description / excerpt
    published = scrapy.Field()  # Publication date (ISO format)

    # Source
    source_feed = scrapy.Field()  # Name of the RSS feed
    feed_url = scrapy.Field()  # URL of the RSS feed
    category = scrapy.Field()  # Category/tag if available

    # Traceability
    scraped_at = scrapy.Field()
    spider_name = scrapy.Field()

