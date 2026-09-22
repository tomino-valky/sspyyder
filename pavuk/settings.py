# Scrapy settings for pavuk project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html

BOT_NAME = "pavuk"

SPIDER_MODULES = ["pavuk.spiders"]
NEWSPIDER_MODULE = "pavuk.spiders"

# --------------------------------------------------------------------------
# Crawl responsibly — identify yourself and be polite
# --------------------------------------------------------------------------

# Transparent User-Agent so server admins know who we are and why
USER_AGENT = (
    "PavukBiotechBot/1.0 "
    "(+https://github.com/tomino-valky/pavuk; "
    "Neurobiology MSc Research at Masaryk University; "
    "contact: 533883@mail.muni.cz)"
)

# Obey robots.txt rules — always
ROBOTSTXT_OBEY = True

# --------------------------------------------------------------------------
# Rate limiting — be a good citizen
# --------------------------------------------------------------------------

# Maximum concurrent requests the engine will perform
CONCURRENT_REQUESTS = 4

# Delay between requests to the same domain (seconds)
DOWNLOAD_DELAY = 1.0

# Max concurrent requests per domain
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# AutoThrottle — dynamically adjusts delay based on server response times
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Uncomment to see throttle stats in the log:
# AUTOTHROTTLE_DEBUG = True

# --------------------------------------------------------------------------
# HTTP Cache — avoid hitting live servers during development
# --------------------------------------------------------------------------

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# --------------------------------------------------------------------------
# Item Pipelines — data processing chain
# --------------------------------------------------------------------------
# Pipelines run in order from lowest to highest number (0-1000)

ITEM_PIPELINES = {
    "pavuk.pipelines.TimestampPipeline": 100,
    "pavuk.pipelines.CleanTextPipeline": 200,
    "pavuk.pipelines.DropIncompletePipeline": 300,
    "pavuk.pipelines.DeduplicationPipeline": 400,
}

# --------------------------------------------------------------------------
# Feed export — default output format
# --------------------------------------------------------------------------

FEEDS = {
    "data/%(name)s_%(time)s.json": {
        "format": "json",
        "encoding": "utf-8",
        "indent": 2,
        "overwrite": True,
    },
}

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

LOG_LEVEL = "INFO"

# --------------------------------------------------------------------------
# Request fingerprinting (Scrapy 2.7+)
# --------------------------------------------------------------------------

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# --------------------------------------------------------------------------
# Zyte Scrapy Cloud
# --------------------------------------------------------------------------
# When running on Scrapy Cloud, disable HTTP cache (Cloud handles storage)
# This is typically set via spider arguments or Scrapy Cloud settings UI:
#   HTTPCACHE_ENABLED = False

