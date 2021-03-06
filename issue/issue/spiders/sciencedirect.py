# -*- coding: utf-8 -*-
import scrapy
import urlparse
from scrapy.http.request import Request
from utils import  Utils

class SciencedirectSpider(scrapy.Spider):
    name = 'sciencedirect'
    allowed_domains = ['http://www.sciencedirect.com/']
    start_urls = [
        'https://www.sciencedirect.com/journal/procedia-engineering/vol/[170-216]/suppl/C'
    ]

    def __init(self, url_file):
        self.url_file = url_file

    def start_requests(self):
        #meta = {"from_url": "from_url", "page": "pages", "issn": "issn"}
        #yield Request("https://www.sciencedirect.com/science/article/pii/S2211601X15000632", self.parse_issue, meta = meta, dont_filter = True)
        #return
        with open(self.url_file, "rb") as f:
            for line in f:
                urls = Utils.parse_generator_str(line.strip())
                for url in urls:
                    yield Request(url, self.parse_confence, dont_filter = True)
                #yield Request(line.strip(), self.parse, dont_filter = True)

    # 会议集合, url: https://www.sciencedirect.com/journal/procedia-computer-science/vol/126/suppl/C
    def parse_confence(self, response):
        source = response.xpath("//*[@id='els-main-title-link']//title/text()").extract_first()
        processding_name = response.xpath("//div[@class='summary-info-header']/h1/a/span/text()").extract_first()
        conference_name = response.xpath("//div[@class='js-title-editors-group']/h2/text()").extract_first()
        author = Utils.get_all_inner_texts(response, "//div[@class='u-margin-xxl-top text-s js-authors']")
        volume = response.xpath("//span[@class='text-s js-vol-issue']/text()").extract_first().replace("Volume ", "").replace(", ", "").strip()
        page_year = Utils.get_all_inner_texts(response, "//span[@class='js-issue-status text-s']")
        page = Utils.regex_extract(page_year, "Pages (.*) \(\d+\)")
        year = Utils.regex_extract(page_year, "Pages .* \((\d+)\)")
        issn = Utils.get_all_inner_texts(response, "//div[@class='u-margin-l-ver u-clr-grey8']/h2").replace("ISSN:", "")
        yield {
            "Source": source,
            "ConferenceUrl": response.url,
            "ConferenceName": conference_name,
            "ConferencePublisher": author,
            "ConferenceVolume": volume,
            "ConferencePage": page,
            "ConferenceYear": year,
            "proceedingName": processding_name,
            "issn": issn
        }

    def parse(self, response):
        articles = response.css(".article-list-items > .article-item")

        issn = response.xpath("//h2[@class='u-margin-bottom-xs text-s u-display-block js-issn']/text()").extract()[-1]
        for article in articles:
            article_url = urlparse.urljoin(response.url, article.xpath(".//a[contains(@class, 'article-content-title')]/@href").extract_first())
            pages = article.xpath(".//dd[2]/text()").extract_first()

            from_url = response.url
            #爬取分页的内容
            if "from_url" in response.meta:
                from_url = response.meta["from_url"]

            meta = {"from_url": from_url, "page": pages, "issn": issn}
            yield response.follow(article_url, self.parse_issue, meta = meta, dont_filter=True)

        if "page_index" in response.meta:
            return

        #处理分页
        total_pages = response.css(".pagination-pages-label::text").extract()
        if total_pages is None or len(total_pages) == 0:
            return
        total_pages = int(total_pages[-1])
        page_index = 2
        while page_index <= total_pages:
            page_url = "%s?page-size=100&page=%s" % (response.url, page_index)
            meta = {"from_url": response.url, "page_index": page_index}
            page_index += 1
            yield response.follow(page_url, self.parse, meta = meta, dont_filter=True)

    def parse_issue(self, response):
        conference = response.css(".publication-title-link::text").extract_first()
        volume = response.css(".publication-volume .size-m span::text").extract_first().replace("Volume", "").strip()
        release_date = response.css(".publication-volume .size-m::text").extract()[1]
        page = response.meta["page"]
        title = " ".join(response.css(".title-text::text").extract())
        author = []
        author_elems = response.css(".author .content")
        for elem in author_elems:
            author_text = " ".join(elem.css(".text::text").extract())
            author.append(author_text)

        author_sup = response.css(".author-ref sup::text").extract()
        doi = response.css(".doi::text").extract_first()
        abstract = "" .join(response.xpath("//div[@class='Abstracts']//p//text()").extract())
        keywords = response.css(".keyword span::text").extract()
        pdf_url = response.css(".download-pdf-link::attr(href)").extract_first()
    
        yield {
            "conference" : conference,
            "volume": volume,
            "release_date" : release_date,
            "page": page,
            "title": title,
            "author": author,
            "author_sup": author_sup,
            "doi": doi,
            "abstract": abstract,
            "keywords" : keywords,
            "pdf_url": pdf_url,
            "from_url": response.meta["from_url"],
            "issn": response.meta["issn"],
            "url": response.url
        }
