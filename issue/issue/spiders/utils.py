# -*- coding: utf-8 -*-
import re
import datetime
import time
import uuid
import os
import json

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
    @origin_date date string crawled
    @return datetime object
    """
    @staticmethod
    def strptime(origin_date):
        print "process time: %s" % origin_date
        dates = origin_date.split()

        month = dates[1]
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
            raise Exception("month not expected: %s" % month)

        month = month_dict[month]
        date_obj = datetime.datetime.strptime("%s-%s-%s" % (dates[2], month, dates[0]), "%Y-%m-%d")
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

        work_dir = "workdir\\" + work_dir

        print "generate_workdir: %s" % work_dir

        os.makedirs(work_dir)

        return work_dir

    @staticmethod
    def format_value(value):
        if type(value) is list:
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

