#!/usr/bin/env python
# -*- coding: utf-8 -*-
import scrapy
import re
import urlparse
import sys
from scrapy.http.request import Request
import requests

reload(sys)
sys.setdefaultencoding('utf8')


class AcsV2(scrapy.Spider):
    name = "AcsV2"
    urls = []

    def __init__(self, urlPath=None, *args, **kwargs):
        super(AcsV2, self).__init__(*args, **kwargs)
        self.urls = self.readText(urlPath)
        print self.urls

    def readText(self, path):
        print "path is %s" % path
        f = file(path, 'r')
        line = f.readline().strip()
        result = []
        while len(line) > 0:
            result.append(line.strip())
            line = f.readline().strip()
        f.close()
        return result

    def start_requests(self):
        urls = self.urls
        meta = {}
        for item in urls:
            search_url = item.split("\t")[0]
            collection = item.split("\t")[1]
            issn = item.split("\t")[2]
            eissn = item.split("\t")[3]
            volume = item.split("\t")[4]
            issue = item.split("\t")[5]
            issue_url = item.split("\t")[6]
            meta['search_url'] = search_url
            meta['collection'] = collection
            meta['issn'] = issn
            meta['eissn'] = eissn
            meta['volume'] = volume
            meta['issue'] = issue
            meta['issue_url'] = issue_url
            yield Request(issue_url, self.parse_issue, meta=meta)

    def parse_issue(self, response):
        meta = {'search_url': response.meta['search_url'],
                'collection': response.meta['collection'],
                'issn': response.meta['issn'],
                'eissn': response.meta['eissn'],
                'issue_url': response.meta['issue_url'],
                'volume': response.meta['volume'],
                'issue': response.meta['issue']
                }
        articlexpaths = response.xpath(".//div[@class='articleGroup']//div[@class='articleBox ']")
        for articlexpath in articlexpaths:
            doi = articlexpath.xpath("@doi").extract_first()
            access_url = urlparse.urljoin(response.url, articlexpath.xpath(
                ".//div[@class='art_title linkable']/a/@href").extract_first().strip())
            title = articlexpath.xpath(".//div[@class='art_title linkable']/a/text()").extract_first().strip()
            authors = articlexpath.xpath(".//span[@class='entryAuthor normal hlFld-ContribAuthor']/text()").extract()
            author = "&"
            if len(authors) != 0:
                author = ";".join(authors)
            pages = articlexpath.xpath(".//span[@class='articlePageRange']/text()").extract_first()
            publish_date = articlexpath.xpath(".//div[@class='epubdate']/text()").extract_first()
            pdf_url = urlparse.urljoin(response.url, articlexpath.xpath(
                ".//a[@title='Download the PDF Full Text']/@href").extract_first().strip())
            meta['doi'] = doi
            meta['title'] = title
            meta['author'] = author
            meta['pages'] = pages
            meta['publish_date'] = publish_date
            meta['pdf_url'] = pdf_url
            meta['access_url'] = access_url
            yield response.follow(access_url, self.parse_article, meta=meta)

    def parse_article(self, response):
        meta = {'search_url': response.meta['search_url'],
                'collection': response.meta['collection'],
                'issn': response.meta['issn'],
                'eissn': response.meta['eissn'],
                'issue_url': response.meta['issue_url'],
                'volume': response.meta['volume'],
                'issue': response.meta['issue'],
                'access_url': response.meta['access_url'],
                'pages': response.meta['pages'],
                'title': response.meta['title'],
                'doi': response.meta['doi'],
                'author': response.meta['author'],
                'publish_date': response.meta['publish_date'],
                'pdf_url': response.meta['pdf_url']
                }

        abstractxpath = response.xpath(".//p[@class='articleBody_abstractText']//text()").extract()
        abstract = "&"
        if len(abstractxpath) != 0:
            abstract = "".join(abstractxpath)
        keywordsxpath = response.xpath(".//a[@class='keyword']/text()").extract()
        keywords = "&"
        if len(keywordsxpath) != 0:
            keywords = ";".join(keywordsxpath)
        meta['keywords'] = keywords
        meta['abstract'] = abstract
        yield meta
