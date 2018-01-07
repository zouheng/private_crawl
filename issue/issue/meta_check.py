#!/bin/python
# -*- coding: utf-8 -*-
import sys
import json
import re
from datetime import datetime
from spiders.utils import Utils
import argparse
import os

"""
Meta检查，同时对key做一些归一化的操作
如果指定了pdf的保存目录，还会自动与pdf文件做join
"""
class MetaCheck(object):
    def __init__(self, args):
        self.args = args

        self.meta_file = args.file
        self.pass_meta_file = args.pass_meta_file
        self.bad_meta_file = args.bad_meta_file
        self.miss_pdf_file = args.miss_pdf_file
        self.convert = args.convert.lower() == "true"

        self.no_access_url = 0
        self.json_fail = 0
        self.incomplete = 0
        self.total = 0
        self.pass_count = 0
        self.dup = 0
        self.pdf_exist = 0
        self.pdf_non_exist = 0

        self.required_key = [
            #"abstracts",
            #sage的 issue和pages有些确实为空。。。
            #"issue",
            #"pages"
            ]
        self.pass_meta_map = {} # used to uniq
        
        #把一些不规则的key, 都归一化为统一的key
        self.key_map = {
            "url" : "access_url",
            "pdf_download" : "pdf_url",
            "date" : "publish_date"
        }

        self._init()

    def __del__(self):
        self.pass_meta_writer.close()
        self.bad_meta_writer.close()
        self.miss_pdf_writer.close()

    def _init(self):
        #reverse_key_map记录了，那些规则的key,可能有哪些不规则的表达
        self.reverse_key_map = {}
        for k, v in self.key_map.items():
            if v in self.reverse_key_map:
                self.reverse_key_map[v].append(k)
            else:
                self.reverse_key_map[v] = [k]
        
        #创建一个workdir
        workdir = Utils.generate_workdir()
        self.pass_meta_file = os.path.join(workdir, self.pass_meta_file)#workdir + "\\" + self.pass_meta_file
        self.bad_meta_file = os.path.join(workdir, self.bad_meta_file)#workdir + "\\" + self.bad_meta_file
        self.miss_pdf_file = os.path.join(workdir, self.miss_pdf_file)#workdir + "\\" + self.miss_pdf_file
        self.pass_meta_writer = open(self.pass_meta_file, "w")
        self.bad_meta_writer = open(self.bad_meta_file, "w")
        self.miss_pdf_writer = open(self.miss_pdf_file, "w")


    def start(self):
        with open(self.meta_file) as f:
            for line in f:
                try:
                    self.total = self.total + 1
                    line = line.strip()
                    json_data = json.loads(line)
                except Exception as e:
                    self.json_fail = self.json_fail + 1
                    continue

                #检查1:access url是最基本的字段了，如果这个都没爬取下来，那连问题都没法定位了
                access_url = self._get_value(json_data, "access_url")
                if access_url == "":
                    self.no_access_url = self.no_access_url + 1
                    continue
                
                #检查2:检查是否采集必备字段
                miss_required_filed = False
                for key in self.required_keys:                
                    value = self._get_value(json_data, key)
                    if value == "":
                        #value为空，表示元数据未采集到此字段
                        bad_record = {}
                        bad_record['reason'] = "%s empty" % key
                        bad_record['access_url'] = access_url
                        self._mark_bad_record(bad_record)
                        self.incomplete = self.incomplete + 1
                        miss_required_filed = True
                        break

                if miss_required_filed:
                    continue
                    
                
                #检查3:检查元数据里面是否有非空字段
                fail = False
                for key, value in json_data.iteritems():
                    key = key.strip(":").strip()
                    value = Utils.format_value(value)
                    if value == "" and key in self.required_key:
                        if key == "publish_year":
                            publish_data = self._get_value(json_data, "publish_date")
                            if publish_data != "":
                                #if publish data is also empty, there is no way to get publish_year
                                json_data["publish_year"] = publish_data.split("-")[0]
                                print "publish year is %s" % json_data["publish_year"]
                                continue

                        bad_record = {}
                        bad_record['reason'] = "%s empty" % key
                        bad_record['access_url'] = access_url
                        self._mark_bad_record(bad_record)
                        self.incomplete = self.incomplete + 1
                        fail = True
                        break

                if fail:
                    continue

                #检查4:补充一些必备字段
                json_data['acquisition_time'] = Utils.current_time()
                publish_year = self._get_value(json_data, "publish_year")
                if publish_year == "":
                    publish_data = self._get_value(json_data, "publish_date")
                    json_data["publish_year"] = publish_data.split("-")[0] 

                if access_url in self.pass_meta_map:
                    title = self._get_value(json_data, "title")
                    if title != self.pass_meta_map[access_url]:
                        #pass
                        raise Exception("same url with different title, not gonna happen :%s" % access_url)
                    self.dup = self.dup + 1
                    continue

                self.pass_count = self.pass_count + 1
                self._mark_success_record(json_data)
                self.pass_meta_map[access_url] = json_data["title"]

        if self.args.pdf_dir is not None:
            print "total: %d, no_access_url: %d, json_fail: %d, incomplete: %d, dup_count: %d, pass_count: %d. pdf_non_exist: %d, pdf_exist_count: %d, pass meta save to: %s, fail meta save to :%s, miss pdf url save to :%s" \
            % (self.total, self.no_access_url, self.json_fail, self.incomplete, self.dup, self.pass_count, self.pdf_non_exist, self.pdf_exist, self.pass_meta_file, self.bad_meta_file, self.miss_pdf_file)
        else:
            print "total: %d, no_access_url: %d, json_fail: %d, incomplete: %d, dup_count: %d, pass_count: %d. pass meta save to: %s, fail meta save to :%s" \
            % (self.total, self.no_access_url, self.json_fail, self.incomplete, self.dup, self.pass_count, self.pass_meta_file, self.bad_meta_file)

    def check_miss_journal(self):
        """
        check miss journal, args:
        python meta_check.py --file xxx --journal_file xxx(xls file) [--source_name wiley] 
        """
        required_args = ['file', 'journal_file']
        help_message = "python meta_check.py --file xxx --journal_file xxx(xls_file)" \
        "[--source_name xxx(f.e: wiley)]"
        self._verify_args(required_args, help_message)
        all_journal_meta = Utils.load_journal_meta(self.args.journal_file)
        should_crawl_journal_meta = {}
        if self.args.source_name is not None:
            for journal, meta in all_journal_meta.iteritems():
                journal_url = meta['journal_url'].lower()
                source_name = self.args.source_name.lower()
                if journal_url.find(source_name) == -1:
                    continue
                else:
                    should_crawl_journal_meta[journal] = meta
        else:
            should_crawl_journal_meta = all_journal_meta

        crawled_journal = {} 
        with open(self.args.file) as fp:
            for line in fp:
                try:
                    json_data = json.loads(line)
                except Exception as e:
                    continue
                journal = json_data['journal'].lower()
                if journal in crawled_journal:
                    crawled_journal[journal] = crawled_journal[journal] + 1
                else:
                    crawled_journal[journal] = 1

        
        for journal, meta in should_crawl_journal_meta.iteritems():
            if journal not in crawled_journal:
               print "miss %s, url: %s" % (journal, "%s/issues" % meta['journal_url'])

    def check_miss_url(self):
        """
        check miss url
        """
        required_args = ['file', 'url_file']
        help_message = "python meta_check.py --file xxx --url_file xxx(should crawl url file)"
        self._verify_args(required_args, help_message)
        download_urls = []
        with open(self.args.file) as f:
            for line in f:
                line = line.strip()
                json_data = json.loads(line)

                url = self._get_value(json_data, "access_url")
                download_urls.append(url)

        #print download_urls

        with open(self.args.url_file) as f: 
            for line in f:
                line = line.strip()
                if line not in download_urls:
                    print "%s" % line

    def _verify_args(self, required_args, help_message):
        print self.args
        for arg in required_args:
            if not hasattr(self.args, arg):
                raise Exception("%s need to be set, usage: %s" % (arg, help_message))

    def _check_key_exist(self, json_data, key):
        """
        这里的key应该是规则的key
        """
        if key in json_data:
            return True
        
        if key in self.reverse_key_map:
            for alias_key in self.reverse_key_map[key]:
                if alias_key in json_data:
                    return True
        
        return False

    def _get_value(self, json_data, key, default = "", convert = True):
        """
        这里的key应该是规则的key
        """
        value = default
        if key in json_data:
            value = json_data[key]
        
        if key in self.reverse_key_map:
            for alias_key in self.reverse_key_map[key]:
                if alias_key in json_data:
                    value =  json_data[alias_key]
                    match_key = alias_key
                    break
        
        ret = Utils.format_value(value, convert)

        #余下，可以针对特定key的value，做一些归一化处理
        if key == "publish_date":
            if type(ret) is not list:
                ret = ret.replace("00:00:00", "")
            else:
                ret[0] = ret[0].replace("00:00:00", "")

        return ret


    def _mark_success_record(self, json_data):
        """
        Mark an success record.

        1. 对Key做一些归一化的工作，同时也可以加一些必备的字段
        2. 如果指定了pdf save dir，则会和pdf文件做拼接

        @param json_data
        """
        publish_data = self._get_value(json_data, "publish_date")
        if "publish_year" not in json_data or json_data["publish_year"] == "":
            #if publish data is also empty, there is no way to get publish_year
            if "publish_date" in json_data:
                json_data["publish_year"] = publish_data.split()[-1]

        #keywords = self._get_value(json_data, "keywords")
        #json_data["keywords"] = keywords.replace("Keywords", "").strip()

        convert_data = {}
        for key, value in json_data.iteritems():
            key = key.strip(":").strip().lower()

            if key in self.key_map:
                key = self.key_map[key]

            value = self._get_value(json_data, key, convert = self.convert) #这里使用_get_value,会对value做一些归一化

            convert_data[key] = value

        if self.args.pdf_dir is not None:
            filename = Utils.get_pdf_filename(json_data)
            pdf_path = os.path.join(self.args.pdf_dir, filename + ".pdf")  
            txt_path = os.path.join(self.args.pdf_dir, filename + ".txt")
            if os.path.exists(pdf_path):
                convert_data["pdf_path"] = filename + ".pdf"
                self.pdf_exist = self.pdf_exist + 1
            elif os.path.exists(txt_path):
                convert_data["pdf_path"] = filename + ".txt"
                self.pdf_exist = self.pdf_exist + 1
            else:
                #print "pdf path(%s) or txt path(%s) not exist" % (pdf_path, txt_path)
                convert_data["pdf_path"] = "wrong"
                self.pdf_non_exist = self.pdf_non_exist + 1
                pdf_link = self._get_value(json_data, "pdf_url")
                if pdf_link == "":
                    raise Exception("cannot get pdf_url from json %s" % json_data)
                self.miss_pdf_writer.write(pdf_link)
                self.miss_pdf_writer.write("\n")
                

        convert_data_str = json.dumps(convert_data)
        self.pass_meta_writer.write(convert_data_str)
        self.pass_meta_writer.write("\n")

    def _mark_bad_record(self, bad_record):
        """
        Mark an bad record

        @param bad_record, format:{"reason: ", "url"}
        """
        bad_record_str = json.dumps(bad_record)
        self.bad_meta_writer.write(bad_record_str)
        self.bad_meta_writer.write("\n")

def parse_init():
    """
    Init argument parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', "--action", default='meta_check', help="action to perform",                              
                choices=['meta_check', 'check_miss_journal', 'check_miss_url'])
    parser.add_argument('-f', "--file", required=True, help="meta file path")
    parser.add_argument('-d', "--pdf_dir", required=False, help="pdf save dir")
    parser.add_argument('-p', "--pass_meta_file", default="pass_meta", help="file to save pass meta")
    parser.add_argument('-b', "--bad_meta_file", default="bad_meta", help="file to save bad meta")
    parser.add_argument('-m', "--miss_pdf_file", default="miss_pdf_file", help="pdf link that fail to download")
    parser.add_argument('-j', "--journal_file", help="journal file, xls format")
    parser.add_argument('-u', "--url_file", help="url_file")
    parser.add_argument('-s', "--source_name", help="source name[f.e: wiley]")
    parser.add_argument('-c', "--convert", default="True", help="whether convert list value")
    return parser

def select_action(action):
    """
    select action
    """
    return {
        'meta_check': meta_check.start,
        'check_miss_journal': meta_check.check_miss_journal,
        'check_miss_url': meta_check.check_miss_url
    }.get(action, meta_check.start)
    
if __name__ == '__main__':
    meta_file = sys.argv[1]
    args = parse_init().parse_args()
    meta_check = MetaCheck(args)
    ret = select_action(args.action)()
    exit(ret)
    meta_check.start()
