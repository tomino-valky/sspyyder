"""
Pavúk — ClinicalTrials.gov Spider ⭐

Scrapes clinical trials from the ClinicalTrials.gov API v2.
Focused on neurobiology/neuroscience conditions by default.

API Docs: https://clinicaltrials.gov/data-api/api

HOW IT WORKS:
=============
ClinicalTrials.gov provides a free, public REST API that returns JSON.
No authentication or API key is needed. The workflow is:

  1. Send a search query with conditions/keywords
  2. API returns a page of matching trials (up to 50 per page)
  3. Follow the "nextPageToken" to get the next page
  4. Repeat until all results are fetched or we hit our limit

USAGE:
======
  # Run with default neurobiology conditions
  scrapy crawl clinicaltrials

  # Search for specific condition
  scrapy crawl clinicaltrials -a condition="Parkinson Disease"

  # Search for specific intervention type
  scrapy crawl clinicaltrials -a intervention="gene therapy"

  # Combine condition and intervention
  scrapy crawl clinicaltrials -a condition="Alzheimer" -a intervention="antibody"

  # Limit number of pages fetched (default: 10)
  scrapy crawl clinicaltrials -a max_pages=5

  # Output to specific file
  scrapy crawl clinicaltrials -O data/trials.json
"""

import scrapy

from pavuk.items import ClinicalTrial


class ClinicalTrialsSpider(scrapy.Spider):
    """Spider for ClinicalTrials.gov API v2.

    Attributes:
        name: Spider identifier used in `scrapy crawl <name>`
        allowed_domains: Restricts requests to these domains only
        custom_settings: Per-spider settings that override project settings

    Spider Arguments (passed via -a flag):
        condition: Disease/condition to search for
        intervention: Intervention type to search for
        status: Trial status filter (comma-separated)
        max_pages: Maximum number of result pages to fetch
    """

    name = "clinicaltrials"
    allowed_domains = ["clinicaltrials.gov"]

    # Per-spider settings — ClinicalTrials.gov allows ~50 req/min
    # NOTE: We disable robots.txt for this spider because we're using
    # the official public REST API, not scraping HTML pages.
    # The robots.txt on clinicaltrials.gov blocks /api/ paths, but
    # the API is explicitly public and intended for programmatic use.
    # See: https://clinicaltrials.gov/data-api/about-api
    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,
    }

    # ── API Configuration ──────────────────────────────────────────────
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    # Default neurobiology-focused conditions to search for.
    # These cover the major neurological disorders and research areas.
    DEFAULT_CONDITIONS = [
        "Alzheimer Disease",
        "Parkinson Disease",
        "Multiple Sclerosis",
        "Amyotrophic Lateral Sclerosis",
        "Huntington Disease",
        "Epilepsy",
        "Glioblastoma",
        "Stroke",
        "Traumatic Brain Injury",
        "Neuropathy",
    ]

    # Fields we want the API to return (reduces response size)
    # See: https://clinicaltrials.gov/data-api/about-api/study-data-structure
    FIELDS = (
        "NCTId,"
        "BriefTitle,"
        "OfficialTitle,"
        "OverallStatus,"
        "Phase,"
        "StudyType,"
        "BriefSummary,"
        "Condition,"
        "InterventionName,"
        "InterventionType,"
        "InterventionDescription,"
        "PrimaryOutcomeMeasure,"
        "EnrollmentCount,"
        "LeadSponsorName,"
        "CollaboratorName,"
        "StartDate,"
        "CompletionDate,"
        "LastUpdatePostDate"
    )

    # ── Spider Initialization ──────────────────────────────────────────

    def __init__(
        self,
        condition=None,
        intervention=None,
        status="RECRUITING,NOT_YET_RECRUITING,ENROLLING_BY_INVITATION",
        max_pages=10,
        *args,
        **kwargs,
    ):
        """Initialize the spider with search parameters.

        Args:
            condition: Condition to search (overrides defaults).
                       Use a single condition string.
            intervention: Intervention to search for (e.g., "gene therapy").
            status: Comma-separated trial statuses to filter by.
            max_pages: Max number of API pages to fetch (50 results each).
        """
        super().__init__(*args, **kwargs)
        self.intervention = intervention
        self.status = status
        self.max_pages = int(max_pages)

        # If user provides a specific condition, use only that.
        # Otherwise, we'll cycle through all default conditions.
        if condition:
            self.conditions = [condition]
        else:
            self.conditions = self.DEFAULT_CONDITIONS

    # ── Entry Point ────────────────────────────────────────────────────

    async def start(self):
        """Generate initial requests — one search per condition.

        Uses ``async def start()`` which is the entry point in Scrapy 2.13+
        (replaces the older ``start_requests()``).

        Each condition gets its own API query. This is better than
        a single OR query because:
        - We get cleaner, more focused results
        - We can track which condition each trial came from
        - We stay well within the 60-minute Zyte free tier limit
        """
        for condition in self.conditions:
            params = {
                "query.cond": condition,
                "filter.overallStatus": self.status,
                "pageSize": 50,
                "fields": self.FIELDS,
            }

            # Add intervention filter if specified
            if self.intervention:
                params["query.intr"] = self.intervention

            url = self._build_url(params)
            self.logger.info(
                f"Searching ClinicalTrials.gov for condition: {condition}"
            )

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={
                    "condition_query": condition,
                    "page": 1,
                },
            )

    # ── Response Parsing ───────────────────────────────────────────────

    def parse(self, response, condition_query, page):
        """Parse the API JSON response and yield ClinicalTrial items.

        The API response structure looks like:
        {
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {"nctId": "NCT05123456", ...},
                        "statusModule": {"overallStatus": "RECRUITING", ...},
                        ...
                    }
                },
                ...
            ],
            "nextPageToken": "abc123"  // null if no more pages
        }
        """
        data = response.json()
        studies = data.get("studies", [])

        self.logger.info(
            f"[{condition_query}] Page {page}: "
            f"received {len(studies)} studies"
        )

        # Yield a ClinicalTrial item for each study
        for study in studies:
            item = self._parse_study(study)
            if item:
                yield item

        # ── Pagination ─────────────────────────────────────────────
        # Follow the nextPageToken if we haven't hit our page limit
        next_token = data.get("nextPageToken")
        if next_token and page < self.max_pages:
            params = {
                "query.cond": condition_query,
                "filter.overallStatus": self.status,
                "pageSize": 50,
                "fields": self.FIELDS,
                "pageToken": next_token,
            }
            if self.intervention:
                params["query.intr"] = self.intervention

            yield scrapy.Request(
                url=self._build_url(params),
                callback=self.parse,
                cb_kwargs={
                    "condition_query": condition_query,
                    "page": page + 1,
                },
            )

    # ── Private Helpers ────────────────────────────────────────────────

    def _parse_study(self, study):
        """Extract fields from a single study JSON object.

        The study object has a deeply nested structure. We carefully
        navigate it with .get() to avoid KeyErrors when fields are
        missing (not all trials have all fields).
        """
        try:
            protocol = study.get("protocolSection", {})

            # Identification
            id_module = protocol.get("identificationModule", {})
            nct_id = id_module.get("nctId")
            brief_title = id_module.get("briefTitle")
            official_title = id_module.get("officialTitle", "")

            # Status
            status_module = protocol.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "")
            start_date_struct = status_module.get("startDateStruct", {})
            start_date = start_date_struct.get("date", "")
            completion_date_struct = status_module.get(
                "completionDateStruct", {}
            )
            completion_date = completion_date_struct.get("date", "")
            last_update = status_module.get("lastUpdatePostDateStruct", {})
            last_updated = last_update.get("date", "")

            # Design
            design_module = protocol.get("designModule", {})
            study_type = design_module.get("studyType", "")
            phases = design_module.get("phases", [])
            phase = ", ".join(phases) if phases else ""
            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment = enrollment_info.get("count", 0)

            # Conditions
            conditions_module = protocol.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])

            # Interventions
            arms_module = protocol.get("armsInterventionsModule", {})
            raw_interventions = arms_module.get("interventions", [])
            interventions = [
                {
                    "type": interv.get("type", ""),
                    "name": interv.get("name", ""),
                    "description": interv.get("description", ""),
                }
                for interv in raw_interventions
            ]

            # Outcomes
            outcomes_module = protocol.get("outcomesModule", {})
            primary_outcomes = [
                outcome.get("measure", "")
                for outcome in outcomes_module.get("primaryOutcomes", [])
            ]

            # Description
            desc_module = protocol.get("descriptionModule", {})
            summary = desc_module.get("briefSummary", "")

            # Sponsor
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            sponsor = lead_sponsor.get("name", "")
            collaborators = [
                c.get("name", "")
                for c in sponsor_module.get("collaborators", [])
            ]

            return ClinicalTrial(
                nct_id=nct_id,
                title=brief_title,
                official_title=official_title,
                status=overall_status,
                phase=phase,
                study_type=study_type,
                conditions=conditions,
                interventions=interventions,
                primary_outcomes=primary_outcomes,
                enrollment=enrollment,
                sponsor=sponsor,
                collaborators=collaborators,
                start_date=start_date,
                completion_date=completion_date,
                last_updated=last_updated,
                summary=summary,
                source_url=f"https://clinicaltrials.gov/study/{nct_id}",
            )

        except Exception as e:
            self.logger.error(f"Error parsing study: {e}")
            return None

    def _build_url(self, params):
        """Build a URL with query parameters.

        We do this manually instead of using urllib.parse.urlencode
        because Scrapy handles URL encoding in its Request object,
        but for readability and logging, an explicit URL is clearer.
        """
        query_parts = []
        for key, value in params.items():
            if value is not None:
                query_parts.append(f"{key}={value}")
        return f"{self.BASE_URL}?{'&'.join(query_parts)}"

