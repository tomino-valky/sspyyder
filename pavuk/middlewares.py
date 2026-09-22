"""
Pavúk — Spider and Downloader Middlewares

Middlewares sit between the Scrapy engine and the spiders/downloaders.
They can modify requests before they're sent and responses before
they reach the spider.

For this project, we keep middlewares minimal — Scrapy's built-in
AutoThrottle and retry middleware handle most of our needs.

Learn more: https://docs.scrapy.org/en/latest/topics/spider-middleware.html
Learn more: https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
"""


class PavukSpiderMiddleware:
    """Custom spider middleware for Pavúk.

    Currently a placeholder — Scrapy's defaults handle our needs.
    You can extend this later to add custom logic, for example:
    - Filtering out responses based on content type
    - Adding custom metadata to requests
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_spider_output(self, response, result, spider):
        for item_or_request in result:
            yield item_or_request

    def process_spider_exception(self, response, exception, spider):
        # Return None to let the default error handling take over
        return None

    def process_start_requests(self, start_requests, spider):
        for request in start_requests:
            yield request


class PavukDownloaderMiddleware:
    """Custom downloader middleware for Pavúk.

    Currently a placeholder — AutoThrottle and retry middleware
    handle rate limiting and error recovery automatically.
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Return None to let the request proceed normally
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        return None

