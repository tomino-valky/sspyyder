# 🕷️ Pavúk — Biotechnology Research Monitor

**Pavúk** (*Slovak for "spider"*) is a Scrapy-based pipeline that aggregates the latest neurobiology and biotechnology research from public APIs into structured JSON data. Built as a master's thesis project at Masaryk University.

## What It Does

Pavúk runs four spiders that collect data from different sources:

| Spider | Source | What It Collects |
|:---|:---|:---|
| `clinicaltrials` | [ClinicalTrials.gov](https://clinicaltrials.gov) API v2 | Active clinical trials for neurological conditions |
| `pubmed` | [PubMed](https://pubmed.ncbi.nlm.nih.gov/) E-utilities | Recent neuroscience research articles |
| `biorxiv` | [bioRxiv](https://www.biorxiv.org/) REST API | Neuroscience preprints before peer review |
| `rss` | Various RSS feeds | Biotech industry news and journal updates |

### Default Neurobiology Focus

The spiders are pre-configured to search for:
- **Conditions:** Alzheimer's, Parkinson's, Multiple Sclerosis, ALS, Huntington's, Epilepsy, Glioblastoma, Stroke, TBI, Neuropathy
- **Topics:** Neuroplasticity, neurotransmitters, blood-brain barrier, neural stem cells, optogenetics, connectomics
- **News:** Nature Neuroscience, Nature Biotechnology, FierceBiotech, BMC Neuroscience

## Quick Start

### 1. Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install Scrapy and dependencies
pip install scrapy feedparser python-dateutil pytest
```

### 2. Run a Spider Locally

```bash
# Run the clinical trials spider (your priority!)
scrapy crawl clinicaltrials

# Search for a specific condition
scrapy crawl clinicaltrials -a condition="Parkinson Disease"

# Run PubMed spider with custom query
scrapy crawl pubmed -a query="optogenetics AND hippocampus"

# Run bioRxiv spider for the last 14 days
scrapy crawl biorxiv -a days=14

# Run RSS feed aggregator
scrapy crawl rss

# Save output to a specific file
scrapy crawl clinicaltrials -O data/trials.json
```

### 3. Run Tests

```bash
python -m pytest tests/ -v
```

## Spider Arguments

Each spider accepts arguments via the `-a` flag:

### clinicaltrials
| Argument | Default | Description |
|:---|:---|:---|
| `condition` | *(10 neuro conditions)* | Disease/condition to search |
| `intervention` | *(none)* | Intervention type (e.g., "gene therapy") |
| `status` | `RECRUITING,NOT_YET_RECRUITING,...` | Trial status filter |
| `max_pages` | `10` | Maximum API pages to fetch |

### pubmed
| Argument | Default | Description |
|:---|:---|:---|
| `query` | *(neurobiology terms)* | PubMed search query |
| `days` | `7` | How many days back to search |
| `max_results` | `100` | Maximum articles to fetch |
| `email` | *(placeholder)* | Your email (required by NCBI) |
| `api_key` | *(none)* | NCBI API key for higher rate limits |

### biorxiv
| Argument | Default | Description |
|:---|:---|:---|
| `server` | `biorxiv` | `biorxiv` or `medrxiv` |
| `days` | `7` | How many days back to search |
| `categories` | *(neuroscience + related)* | Comma-separated categories, or `all` |
| `max_pages` | `20` | Maximum API pages to fetch |

### rss
| Argument | Default | Description |
|:---|:---|:---|
| `days` | `7` | How many days back to include |
| `extra_feed` | *(none)* | Additional RSS feed URL |

## Deploy to Zyte Scrapy Cloud

### 1. Get Your Project ID

1. Log into [app.zyte.com](https://app.zyte.com)
2. Create a new Scrapy Cloud project
3. Copy the numeric Project ID from the URL (e.g., `app.zyte.com/p/123456`)
4. Edit `scrapinghub.yml` and replace `YOUR_PROJECT_ID` with your ID

### 2. Install and Configure shub

```bash
pip install shub
shub login   # Enter your API key when prompted
```

### 3. Deploy

```bash
shub deploy
```

### 4. Run on Scrapy Cloud

```bash
# Run a spider
shub schedule clinicaltrials

# Watch the log
shub log -f <job_id>
```

## Automated Daily Crawls (GitHub Actions)

The repo includes a GitHub Actions workflow that automatically:
1. Triggers all four spiders on Zyte Scrapy Cloud daily at 06:00 UTC
2. Waits for each job to complete
3. Downloads the scraped items as JSON
4. Commits the data to the `data/` directory

### Setup

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add two repository secrets:
   - `ZYTE_API_KEY` — Your API key from [app.zyte.com/account/apikey](https://app.zyte.com/account/apikey)
   - `ZYTE_PROJECT_ID` — Your numeric project ID

The workflow will run daily, or you can trigger it manually from the **Actions** tab.

## Project Structure

```
pavuk/
├── scrapy.cfg                         # Scrapy project config
├── scrapinghub.yml                    # Zyte deployment config
├── requirements.txt                   # Cloud dependencies
├── .gitignore
├── README.md
├── pavuk/
│   ├── __init__.py
│   ├── items.py                       # Data models (4 item types)
│   ├── pipelines.py                   # Clean → Validate → Deduplicate
│   ├── middlewares.py                 # Custom middleware (placeholder)
│   ├── settings.py                    # Polite crawling configuration
│   └── spiders/
│       ├── clinicaltrials_spider.py   # ClinicalTrials.gov API v2
│       ├── pubmed_spider.py           # PubMed E-utilities
│       ├── biorxiv_spider.py          # bioRxiv REST API
│       └── rss_spider.py             # RSS feed aggregator
├── .github/workflows/
│   └── scheduled_crawl.yml           # Daily cron + data export
├── data/                              # Exported JSON data
└── tests/
    └── test_items.py                  # Item & pipeline tests
```

## Ethical Scraping

This project follows responsible scraping practices:
- ✅ Uses **official public APIs** — no HTML scraping
- ✅ **robots.txt** compliance enabled
- ✅ **AutoThrottle** dynamically adjusts request rate
- ✅ **Rate limiting** respects each API's published limits
- ✅ Transparent **User-Agent** with contact information
- ✅ **HTTP caching** during development to avoid redundant requests

## TODO: Future Plans

- [ ] **GitHub Pages site** to display scraped data as a browsable news feed
- [ ] Keyword-based **alerting** for specific research topics
- [ ] **Weekly digest** email or RSS feed of aggregated results
- [ ] Full-text search across abstracts and summaries

## License

This project is for educational purposes as part of a Biotechnology MSc at Masaryk University.

---

*Built with [Scrapy](https://scrapy.org/) and deployed on [Zyte Scrapy Cloud](https://www.zyte.com/scrapy-cloud/).*

