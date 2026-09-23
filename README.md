# 🕷️ Pawúk — Biotechnology & Equine Research Monitor

**Pawúk** is a Scrapy-based pipeline that aggregates the latest neurobiology, equine science, and biotechnology research from public APIs into structured JSON data. Developed as a side project to understand web crawlers and data aggregation better.

## What It Does

Pawúk runs four spiders that collect data from different sources:

| Spider | Source | What It Collects |
|:---|:---|:---|
| `clinicaltrials` | [ClinicalTrials.gov](https://clinicaltrials.gov) API v2 | Active clinical trials for neurological conditions |
| `pubmed` | [PubMed](https://pubmed.ncbi.nlm.nih.gov/) E-utilities | Recent neuroscience research articles |
| `biorxiv` | [bioRxiv](https://www.biorxiv.org/) REST API | Neuroscience preprints before peer review |
| `rss` | Various RSS Feeds | Latest industry news (Nature, FierceBiotech, etc.) |
| `equine` | [PubMed](https://pubmed.ncbi.nlm.nih.gov/) E-utilities | Recent equine and horse-related research articles |

## Features

- **Polite Crawling:** Uses delays, AutoThrottle, and respects API constraints.
- **Pipeline Processing:** Cleans text, parses timestamps, drops incomplete records, and deduplicates items.
- **Automated Dashboard:** Generates a beautiful HTML dashboard (`index.html`) directly from the scraped data using `build_dashboard.py`.
- **GitHub Actions Automation:** Runs automatically every day to keep data fresh without a server.

## Quickstart

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a spider:**
   ```bash
   scrapy crawl pubmed -O data/pubmed.json
   scrapy crawl equine -O data/equine.json
   ```

3. **Rebuild the dashboard:**
   ```bash
   python build_dashboard.py
   ```
   Then open `index.html` in your browser.
