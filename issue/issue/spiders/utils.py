# -*- coding: utf-8 -*-
import re
import datetime
import time
import uuid
import os
import json
import xlrd
import sys
"""
Provide some utils function to crawl web data
"""
class Utils(object):
    """
    Select element by content, if not find, throw exception

    @param selected_content: 可以用|分隔
    """
    @staticmethod
    def select_element_by_content(response, xpath, selected_content):
        selected_contents = selected_content.split('|')
        for content in selected_contents:
            elem = Utils._select_element_by_content_inner(response, xpath, content)
            if elem is not None:
                return elem

        raise Exception("can not found element(%s) with content(%s)" % (xpath, selected_content))
        
    """
    获取元素下面的所有文本内容，排除其他内嵌标签的影响。
    xpath里面不需要写"//text()"，其实实现的秘诀就是用//text()而不是/text()
    具体可以参考这篇问答：https://stackoverflow.com/questions/10618016/html-xpath-extracting-text-mixed-in-with-multiple-tags
    """
    @staticmethod
    def get_all_inner_texts(response, xpath, split_char = '\n'):
        elems = response.xpath(xpath)
        content = ""
        for elem in elems:
            # inner text should strip newchar and join with space
            elem_text = " ".join([v.replace("\n", " ") for v in elem.xpath(".//text()").extract()])
            content = content + elem_text + split_char
        content = content.strip()
        content = re.sub(' +', ' ', content)
        return content


    @staticmethod
    def replcace_not_ascii(origin, replace_char=' '):
        result = re.sub(r'[^\x00-\x7F]+', replace_char, origin)
        result = re.sub(' +', ' ', result)
        return result

    @staticmethod
    def _select_element_by_content_inner(response, xpath, selected_content):
        found = False
        elements = response.xpath(xpath)
        for element in elements:
            if element.xpath("text()").extract_first().strip() == selected_content:
                selected_elemment = element
                found = True

        if not found:
            return None

        return selected_elemment

    """
    Parse date from string
    @origin_date: date string crawled, possible format:
        1: November 1, 2017
        2: 1 November 2017
    @return datetime object
    """
    @staticmethod
    def strptime(origin_date):
        origin_date = origin_date.replace(",", "")
        dates = origin_date.split()

        month = dates[1]
        day = dates[0]
        month_dict = {
                'Jan' : 1, 
                'January' : 1,
                'Feb' : 2, 
                'February' : 2,
                'Mar' : 3, 
                'March' :3,
                'Apr' : 4, 
                'April' : 4,
                'May' : 5, 
                'June' : 6, 
                'July' : 7, 
                'Aug': 8,
                'August' : 8,
                'Sept' : 9, 
                'Sep' : 9, 
                'September' : 9,
                'Oct' : 10, 
                'October' : 10,
                'Nov' : 11, 
                'November' : 11,
                'Dec' : 12,
                'December': 12}

        if month not in month_dict:
            month = dates[0]
            day = dates[1]
            if month not in month_dict:
                raise Exception("month not expected: %s" % month)

        month = month_dict[month]
        date_obj = datetime.datetime.strptime("%s-%s-%s" % (dates[2], month, day), "%Y-%m-%d")
        return date_obj

    @staticmethod
    def get_pdf_filename(json_data):
        """
        get pdf filename from a json meta data
        """
        guoyan_pattern = re.compile(".*docid=(?P<docid>-?\d+)&.*")
        if "doi" not in json_data:
            access_url = json_data["access_url"]
            #国研网没有doi，从access_url里面获取docid
            match = guoyan_pattern.match(access_url)
            if match:
                doi = str(match.group("docid"))
            else:
                raise Exception("connot get doi from json_data, %s" % json_data)
        else:
            doi = Utils.format_value(json_data['doi'])
        return Utils.doi_to_filname(doi)
    
    @staticmethod
    def doi_to_filname(doi):
        doi = doi.replace("http://dx.doi.org/", "")
        doi = doi.replace("https://dx.doi.org/", "")
        doi = doi.replace("http://doi.org/", "")
        doi = doi.replace("https://doi.org/", "")
        doi = doi.replace("/", "_")
        if doi == "":
            raise Exception("Unexception doi: %s" % doi)
        return doi

    @staticmethod
    def current_time():
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    @staticmethod
    def extract_with_xpath(root, xpath_str, default_value = ""):
        try:
            result = root.xpath(xpath_str).extract_first().strip()
        except Exception as e:
            result = default_value

        return result

    @staticmethod
    def extract_all_with_xpath(root, xpath_str, default_value = ""):
        try:
            result = "".join(root.xpath(xpath_str).extract())
            result = result.strip()
        except Exception as e:
            result = default_value

        return result

    @staticmethod
    def generate_workdir(prefix=""):
        work_dir = str(uuid.uuid1())
        if prefix != "":
            work_dir = prefix + "_" + work_dir

        work_dir = os.path.join("workdir", work_dir)#"workdir\\" + work_dir

        print "generate_workdir: %s" % work_dir

        os.makedirs(work_dir)

        return work_dir

    @staticmethod
    def format_value(value, convert=True):
        if type(value) is list:
            if not convert:
                return value

            if value[0] is None:
                value = ""
            else:
                value = ",".join(value)

        if value is None:
            value = ""

        value = value.strip()
        return value

    @staticmethod
    def is_json_string(str):
        try:
            json_data = json.loads(str)
        except Exception:
            return False
        return True

    @staticmethod
    def extract_chars(origin, start_chars, end_chars):
        try:
            start_index = origin.index(start_chars) + len(start_chars)
            end_index = origin.index(end_chars)
        except Exception as e:
            print "origin is: %s" % origin
            print "start_chars: %s" % start_chars
            return ""
        return origin[start_index:end_index]

    @staticmethod
    def _format_authors(json_data, authors, author_sups, author_affliication):
        """
        @param author_sups 目前不支持一个作者多个机构
        """
        if len(authors) != len(author_sups):
            raise Exception("len of authors(%d), author_sups(%d) not equal" %
                (len(authors), len(author_sups), len(author_affliication)))

        author_text = "|".join(authors)
        author_affliication_text = ""
        for sup in author_sups:
            try:
                affliication = author_affliication[int(sup) - 1]
            except Exception as e:
                #还有可能作者引用的机构不存在的情况,比如：
                #https://www.intechopen.com/books/advances-in-solid-state-lasers-development-and-applications/laser-driven-proton-acceleration-research-and-development
                print "get afflication error: %s" % json_data["url"]
                affliication = "unkown"
            affliication = re.sub('\[\d+\]', '', affliication)
            author_affliication_text += affliication + "|"

        author_affliication_text = author_affliication_text.strip("|")
        json_data['author'] = author_text
        json_data['author_affliication'] = author_affliication_text
        return json_data

    def load_journal_meta(all_journal_meta_xls):
        """
        Load all journal meta info from xls file

        Return List
        """
        all_journal_meta = {}
        data = xlrd.open_workbook(all_journal_meta_xls)

        #TODO 其他需求journal元数据表可能不是这样
        table = data.sheets()[2] #3rd sheet is main sheet
        nrows = table.nrows
        ncols = table.ncols
        for i in xrange(0,nrows):
            #TODO 前两行没用，其他需求可能不适用
            if (i <= 1):
                continue

            rowValues= table.row_values(i)

            journal = rowValues[9].lower().strip()
            if journal in all_journal_meta:
               raise Exception("journal find multiple meta info: %s" % journal)

            all_journal_meta[journal] = {
            'journal_id': rowValues[0],
            'issn': rowValues[1],
            'eissn': rowValues[2],
            'country': rowValues[5],
            'language': rowValues[6],
            'license_type': rowValues[17],
            'license_text': rowValues[18],
            'oa_type': rowValues[19], 
            'available_time': rowValues[20],
            'journal_url': rowValues[23],
            'platform_url': rowValues[27],
            'system_id': rowValues[40],
            'collection_id': rowValues[43],
            'source_id': rowValues[44]}
        return all_journal_meta
