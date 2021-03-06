# -*- coding: utf-8 -*-
# 2019-06-02
# Aosis期刊的爬虫，支持续采
import scrapy
import urlparse
from utils import Utils
from scrapy.http.request import Request
import re
import json
import urlparse

class AosisSpider(scrapy.Spider):
    name = 'aosis'

    """
    @param start_year 爬起的期刊发布日期>=start_year, 为None时没有此限制。
    """
    def __init__(self, url_file=None, start_year=None):
        self.url_file = url_file
        if start_year is None:
            self.start_year = 0
        else:
            self.start_year = start_year

    def start_requests(self):
        # 调试
        #meta = {"journal_url": "url"}
        #url = "http://www.satnt.ac.za/index.php/satnt/article/view/686"
        #yield Request(url, self.crawl_issue_info, meta = meta, dont_filter=True)
        #return

        with open(self.url_file, "rb") as f:
            for line in f:
                meta = {"journal_url": line.strip()}
                journal_issue_url = "%s/issue/archive/" % line.strip()
                yield Request(journal_issue_url, self.crawl_homepage, meta = meta, dont_filter=True)

    def crawl_homepage(self, response):
        journals = response.xpath("//div[@class='issueDescription']")
        for journal in journals:
            link_text = journal.xpath("./h4/a/text()").extract_first().strip()
            year = Utils.regex_extract(link_text, "Vol.*\((\d+)\).*")
            url = urlparse.urljoin(response.url, journal.xpath("./h4/a/@href").extract_first())
            if year >= self.start_year:
                meta = {"journal_url": response.meta["journal_url"]}
                yield Request(url, self.crawl_journal, meta = meta)

        if len(journals) == 0:
            #另一种case，比如: http://www.satnt.ac.za/index.php/satnt/issue/archive/
            journals = response.xpath(".//ul[@class='issues_archive']/li")
            for journal in journals:
                link_text = journal.xpath(".//a[@class='title']/text()").extract_first().strip()
                year = Utils.regex_extract(link_text, "Vol.*\((\d+)\).*").strip()
                url = urlparse.urljoin(response.url, journal.xpath(".//a[@class='title']/@href").extract_first())
                if year >= self.start_year:
                    meta = {"journal_url": response.meta["journal_url"]}
                    yield Request(url, self.crawl_journal, meta = meta)

    def crawl_journal(self, response):
        issues = response.xpath("//div[@class='tocTitle']")
        for issue in issues:
            url = issue.xpath("./a/@href").extract_first()
            meta = {"journal_url": response.meta["journal_url"]}
            yield Request(url, self.crawl_issue_info, meta = meta)

        if len(issues) == 0:
            issues = response.xpath("//ul[@class='cmp_article_list articles']/li")
            for issue in issues:
                url = issue.xpath(".//div[@class='title']/a/@href").extract_first()
                meta = {"journal_url": response.meta["journal_url"]}
                yield Request(url, self.crawl_issue_info, meta = meta)
            

    def crawl_issue_info(self, response):
        article_title = Utils.get_all_inner_texts(response, ".//h3[@class='abstract_title']")

        if article_title == "":
            #另外的Case， 如:http://www.satnt.ac.za/index.php/satnt/article/view/686
            article_title = Utils.get_all_inner_texts(response, ".//h1[@class='page_title']")
            
            authors = response.xpath("//ul[@class='item authors']/li")
            index = 0
            author = ""
            author_ins_list = []
            for author_elem in authors:
                author_name = author_elem.xpath("./span[@class='name']/text()").extract_first().strip()
                author_ins = author_elem.xpath("./span[@class='affiliation']/text()").extract_first().strip()

                if index != 0:
                    author += ";"

                if author_ins is not None:
                    if author_ins in author_ins_list:
                        sup = author_ins_list.index(author_ins) + 1
                    else:
                        author_ins_list.append(author_ins)
                        sup = len(author_ins_list)

                    author += "%s^%s" % (author_name, sup)
                else:
                    author += "%s" % (author_name)

                index += 1

            index = 0
            auth_institution = ""
            for affiliation in author_ins_list:
                if index != 0:
                    auth_institution += ";"

                auth_institution += "%s^%s" % (affiliation, index + 1)
                index += 1

            doi = Utils.extract_text_with_xpath(response, "//span[@class='orcid']/a")

            volume_issue = response.xpath("//div[@class='item issue']//a[@class='title']/text()").extract_first()
            source_year = Utils.regex_extract(volume_issue, "Vol.*\((\d+)\).*")
            source_volume = Utils.regex_extract(volume_issue, "Vol (\d+)")
            source_issue = Utils.regex_extract(volume_issue, "No (\d+)")

            article_abstract = Utils.get_all_inner_texts(response, "//div[@class='item abstract']").replace("Abstract", "").strip()
            keyword = Utils.get_all_inner_texts(response, "//div[@class='item keywords']//span[@class='value']")
            file_path = response.url
            download_path = urlparse.urljoin(response.url, response.xpath(".//a[@class='obj_galley_link pdf']/@href").extract_first())
            process_date = Utils.current_date()

        else:
            #作者
            authors = Utils.get_all_inner_texts(response, "//div[@id='authorString']").split(",")
            affiliation_elem = Utils.select_element_by_content(response, "//div[@id='content']/div", "About the author")
            affiliations = affiliation_elem.xpath("./text()").extract()
            affilation_map = {}
            affiliation_list = []
            for affiliation in affiliations:
                affiliation = Utils.remove_separator(affiliation)
                if affiliation == "":
                    continue
                elems = affiliation.split(",")
                author = elems[0]
                affiliation = ",".join(elems[1:])
                affilation_map[author] = affiliation
                if affiliation not in affiliation_list:
                    affiliation_list.append(affiliation)

            # 生成作者和作者机构
            index = 0
            author = ""
            for author_text in authors:
                author_text = Utils.remove_separator(author_text)
                if index != 0:
                    author += ";"

                if author_text in affilation_map:
                    sup = affiliation_list.index(affilation_map[author_text]) + 1
                    author += "%s^%s" % (author_text, sup)
                else:
                    author += author_text

                index += 1

            index = 0
            auth_institution = ""
            for affiliation in affiliation_list:
                if index != 0:
                    auth_institution += ";"

                auth_institution += "%s^%s" % (affiliation, index + 1)
                index += 1

            doi = response.xpath("//a[@id='pub-id::doi']/@href").extract_first()

            identity = response.xpath("//div[@id='breadcrumb']/a")[1].xpath("./text()").extract_first()
            source_year = Utils.regex_extract(identity, "Vol.*\((\d+)\).*")
            source_volume = Utils.regex_extract(identity, "Vol (\d+)")
            source_issue = Utils.regex_extract(identity, "No (\d+)")

            #info_text = Utils.get_all_inner_texts(response, "//div[@id='authorString']/following-sibling::div")

            article_abstract = Utils.get_all_inner_texts(response, "//div[@id='articleAbstract']").replace("Abstract", "").strip()
            keyword = Utils.get_all_inner_texts(response, "//div[@id='articleSubject']/div")
            file_path = response.url

            #pdf连接
            pdf_elem = Utils.select_element_by_content(response, "//div[@id='articleFullText']/a", "PDF")
            download_path = urlparse.urljoin(response.url, pdf_elem.xpath("./@href").extract_first())

            process_date = Utils.current_date()

        yield {
            "article_title" : article_title,
            "author": author,
            "auth_institution": auth_institution,
            "doi": doi,
            "source_year": source_year,
            "source_volume": source_volume,
            "source_issue": source_issue,
            "article_abstract": article_abstract,
            "keyword": keyword,
            "file_path": file_path,
            "download_path": download_path,
            "process_date": process_date,
            "journal_url" : response.meta["journal_url"]
        }
