# -*- coding: utf-8 -*- 
import os
import sys
import json
import time
import xlrd
import datetime
import re
import urlparse
from unidecode import unidecode
from xml.dom import minidom
from mysql_helper import MySQLHelper
reload(sys)
sys.setdefaultencoding('utf8')

class Json2Xml:
    """Convert metadata result crawled by scrapy to xml
    """
    def __init__(self, all_journal_meta_xls, json_file, save_file, table_suffix = None, use_new_journal = None, checked_table = None):
        self.json_file = json_file
        self.save_file = save_file
        self.today = "20180820"#time.strftime('%Y%m%d', time.localtime(time.time() - 24*3600))
        self.now = time.strftime('%Y-%m-%dT00:00:00',time.localtime(time.time() - 24 * 3600))
        if table_suffix is None:
            table_suffix = self.today
        self.table_suffix = table_suffix
        self.use_new_journal = use_new_journal
        self.checked_table = checked_table

        self.all_journal_meta = {}
        #以防某些元数据爬取不到journal name，从excel里面获取journal url与journal name的对应关系
        self.journal_url_to_name = {}
        self.load_journal_meta(all_journal_meta_xls)
        self.journal_ids = {}
        self.next_article_id= 1
        self.current_url = ""
        self.journal_name_map = {
            "C" : "C Journal of Carbon Research",
            "IJERPH" : "International Journal of Environmental Research and Public Health",
            "IJFS" : "International Journal of Financial Studies",
            "IJGI" : "ISPRS International Journal of Geo-Information",
            "IJMS" : "International Journal of Molecular Sciences",
            "J. INTELL." : "Journal of Intelligence",
            "JCDD" : "Journal of Cardiovascular Development and Disease",
            "JCM" : "Journal of Clinical Medicine",
            "JDB" : "Journal of Developmental Biology",
            "JFB" : "Journal of Functional Biomaterials",
            "JLPEA" : "Journal of Low Power Electronics and Applications",
            "JMSE" : "Journal of Marine Science and Engineering",
            "JPM" : "Journal of Personalized Medicine",
            "JRFM" : "Journal of Risk and Financial Management",
            "JSAN" : "Journal of Sensor and Actuator Networks",
            "INTEGR MED INT" : "Integrative Medicine International",
            "ASWAN HEART CENTRE SCIENCE & PRACTICE SERIES" : "Aswan Heart Centre Science and Practice Series",
            "Audiol Neurotol Extra" : "Audiology and Neurotology Extra",
            "Case Rep Dermatol" : "Case Reports in Dermatology",
            "Case Rep Gastroenterol" : "Case Reports in Gastroenterology",
            "Case Rep Neurol" : "Case Reports in Neurology",
            "Case Rep Oncol" : "Case Reports in Oncology",
            "Case Rep Ophthalmol" : "Case Reports in Ophthalmology",
            "Cerebrovasc Dis Extra" : "Cerebrovascular Diseases Extra",
            "Dement Geriatr Cogn Disord Extra" : "Dementia and Geriatric Cognitive Disorders Extra",
            "Med Epigenet" : "Medical Epigenetics",
            "Transactions of the London Mathematical Society" : "Transactions London Mathematical Society",
            "Progress of Theoretical and Experimental Physics" : "Prog. Theor. Exp. Phys.",
            "International Journal of Low-Carbon Technologies" : "Intl Jnl of Low-Carbon Technologies",
            "biology open" : "Biology Open",
            "Koedoe" : "Koedoe - African Protected Area Conservation and Science",
            "In die Skriflig/In Luce Verbi" : "In die Skriflig",
            "South African Journal of Radiology" : "SA Journal of Radiology",
            "The African Journal of Primary Health & Family Medicine" : "African Journal of Primary Health Care & Family Medicine",
            "REDIMAT" : "Journal of Research in Mathematics Education",
            "RISE - International Journal of Sociology of Education" : "International Journal of Sociology of Education",
            "RIMCIS - International and Multidisciplinary Journal of Social Sciences" : "International and Multidisciplinary Journal of Social Sciences",
            "C&SC - Comunication & Social Change" : "Communication & Social Change",
            "REMIE - Multidisciplinary Journal of Educational Research" : "Multidisciplinary Journal of Educational Research",
            "DEMESCI International Journal of Deliberative Mechanisms in Science" : "The Journal of Deliberative Mechanisms in Science",
            "GÃ©neros - Multidisciplinary Journal of Gender Studies" : "Multidisciplinary Journal of Gender Studies",
            "HSE - Social and Education History" : "Social and Education History",
            "International Journal of Educational Psychology - IJEP" : "International Journal of Educational Psychology",
            "RASP - Research on Ageing and Social Policy" : "Research on Ageing and Social Policy",
            "MSC - Masculinities and social change" : "Masculinities & Social Change",
            "Resumen" : "Social and Education History",
            "Biotechnology & Biotechnological Equipment" : "Biotechnology and Biotechnological Equipment",
            "Ciencia y Tecnologia Alimentaria" : "CyTA - Journal of Food",
            u"Revista mexicana de fitopatologÃ­a" : "Revista Mexicana de Fitopatologia",
            u"Pesquisa AgropecuÃ¡ria Brasileira" : "Pesquisa Agropecuaria Brasileira",
            #u"Arquivo Brasileiro de Medicina VeterinÃ¡ria e Zootecnia" : "Arquivo Brasileiro de Medicina Veterinaria e Zootecnia",
            "GCB Bioenergy" : "Global Change Biology Bioenergy",
            "Energy Technology & Policy": "Energy and Policy Research",
            u"RodriguÃ©sia": "Rodriguésia",
            u"Ambiente ConstruÃ­do": "Ambiente Construído",
            u"Einstein (SÃ£o Paulo)": "Einstein (São Paulo)",
            u"Revista GaÃºcha de Enfermagem": "Revista Gaúcha de Enfermagem",
            u"RodriguÃ©sia": "Rodriguésia",
            u"SequÃªncia (FlorianÃ³polis)": "Sequência (Florianópolis)",
            u"Pesquisa AgropecuÃ¡ria Tropical": "Pesquisa Agropecuária Brasileira",
            u'arquivo brasileiro de medicina veterinaria e zootecnia': "Revista Brasileira de Zootecnia",
            'Arquivo Brasileiro de Medicina VeterinÃ¡ria e Zootecnia': "Revista Brasileira de Zootecnia",
            'IJNS': "International Journal of Neonatal Screening",
            'J. Imaging': "Journal of Imaging",
            'ncRNA': 'Non-Coding RNA',
            'JoF': 'Journal of Fungi',
            u'Anais da Academia Brasileira de CiÃªncias': 'Anais da Academia Brasileira de Ciencias',
            u'ABCD. Arquivos Brasileiros de Cirurgia Digestiva (SAPSo Paulo)': 'ABCD. Arquivos Brasileiros de Cirurgia Digestiva (So Paulo)',
            u'Acta OrtopA(c)dica Brasileira': "Acta Ortopédica Brasileira",
            u'Anais da Academia Brasileira de CiAancias': "Anais da Academia Brasileira de Ciencias",
            u"Archives of Clinical Psychiatry (SAPSo Paulo)": "Archives of Clinical Psychiatry (So Paulo)",
            u"PapA(c)is Avulsos de Zoologia": "Papeis Avulsos de Zoologia (Sao Paulo)",
            u"Food Science and Technology": "Food Science and Technology (Campinas)",
            u"Papeis Avulsos de Zoologia": "Papeis Avulsos de Zoologia (Sao Paulo)",
            u"REAd. Revista Eletronica de Administracao (Porto Alegre)": "REAd. Revista Eletrnica de Administrao (Porto Alegre)",
            u"Revista Brasileira de Estudos de Populacao": "Revista Brasileira de Estudos de Populao",
            u"Revista de Administracao (Sao Paulo)": "Revista de Administrao (So Paulo)",
            u"Revista de Economia Contemporanea": "Revista de Economia Contempornea",
            u"Revista de Nutricao": "Revista de Nutrio",
            u"Revista do Instituto de Medicina Tropical de Sao Paulo": "Revista do Instituto de Medicina Tropical de So Paulo",
            u"Brazilian Journal of Nephrology": "Jornal Brasileiro de Nefrologia",
            u"Brazilian Journal of Political Economy": "Revista de Economia Politica",
            u"Brazilian Journal of Poultry Science": "Revista Brasileira de Ciencia Avicola",
            u"Einstein (Sao Paulo)": "Einstein (So Paulo)",
            u"Servico Social & Sociedade": "Servio Social & Sociedade",
            u"TEMA (Sao Carlos)": "TEMA (So Carlos)",
            "B": "Biotechnology and Biotechnological Equipment",
            "J": "Journal of Applied Animal Research",
            "G": "Geomatics, Natural Hazards and Risk",
            "C": "CyTA - Journal of Food",
            "E": "European Journal of Entomology",
            u"c journal of carbon research": "C – Journal of Carbon Research",
            "A": "ASN Neuro",
            "V": "Virology: Research and Treatment",
            "CompCytogen": "Comparative Cytogenetics",
            "Comparative Cyrogenetics": "Comparative Cytogenetics",
            "Radiographer": "Journal of Medical Radiation Sciences"
        }

        for k,v in self.journal_name_map.items():
            self.journal_name_map[k.upper()] = v

        self._init_db()

        self.checked_urls = []
        if self.checked_table:
            print "load checked_table"
            self.checked_urls = self._load_checked_urls()

    def __del__(self):
        self.mysql_helper.close()

    """
    Init mysql database and table:
    1. create database oa if not exist
    2. create table article_info if not exist
    3. create table article_author if not exist
    """
    def _init_db(self):
            self.mysql_helper = MySQLHelper("127.0.0.1", "root", "123456")
            self.oa_database = "oa_%s" % self.table_suffix
            self.article_table = "article_info"
            self.author_table = "article_author"
            self.mysql_helper.create_database(self.oa_database)
            self.mysql_helper.use_db(self.oa_database)
            create_table_sql = "create table if not exists %s(" \
                                "collection_id varchar(50) NOT NULL," \
                                "source_id varchar(50) NOT NULL,"\
                                "system_id varchar(50) NOT NULL,"\
                                "ro_id varchar(50) NOT NULL,"\
                                "work_id varchar(50) NOT NULL,"\
                                "doi varchar(100) NOT NULL,"\
                                "work_title text NOT NULL,"\
                                "issn varchar(20),"\
                                "eissn varchar(20),"\
                                "collection_title varchar(100) NOT NULL,"\
                                "platform_url varchar(100) NOT NULL,"\
                                "source_name varchar(100) NOT NULL,"\
                                "keywords text,"\
                                "language varchar(20) NOT NULL,"\
                                "abstract text,"\
                                "country varchar(20) NOT NULL,"\
                                "publish_year varchar(20) NOT NULL,"\
                                "publish_date varchar(20) NOT NULL,"\
                                "volume varchar(100) NOT NULL,"\
                                "issue varchar(100) NOT NULL,"\
                                "access_url varchar(300) NOT NULL,"\
                                "license_text text,"\
                                "license_url varchar(100),"\
                                "copyright text,"\
                                "ro_title varchar(100) NOT NULL,"\
                                "xml_uri varchar(300) NOT NULL,"\
                                "pdf_uri varchar(500) NOT NULL,"\
                                "pdf_access_url varchar(500) NOT NULL,"\
                                "creator varchar(20) NOT NULL,"\
                                "create_time datetime NOT NULL,"\
                                "finished tinyint(1) NOT NULL DEFAULT 0,"\
                                "extra varchar(50) comment 'extra info',"\
                                "start_page varchar(10),"\
                                "end_page varchar(10),"\
                                "total_page_number varchar(10),"\
                                "PRIMARY KEY(work_id)) DEFAULT CHARSET=utf8;" % self.article_table
            self.mysql_helper.execute(create_table_sql)

            author_create_table_sql = "create table if not exists %s("\
                                      "work_id varchar(50) NOT NULL,"\
                                      "author_name varchar(200) NOT NULL,"\
                                      "institution_name varchar(1000)"\
                                      ") DEFAULT CHARSET=utf8;" % self.author_table
                                      #"PRIMARY KEY(work_id, author_name, institution_name)) DEFAULT CHARSET=utf8;" % self.author_table
            self.mysql_helper.execute(author_create_table_sql)

    def _load_checked_urls(self):
        sql = "select access_url from `%s`" % self.checked_table
        return [elem["access_url"] for elem in self.mysql_helper.query_all(sql)]

    def convert(self):
        #print self.all_journal_meta["polymers"]
        #sys.exit(0)
        output_meta_file_path = "%s/output_meta.jl" % self.save_file
        author_meta_file_path = "%s/author_meta.txt" % self.save_file

        self.output_meta_file = open(output_meta_file_path, 'w+')
        self.author_meta_file = open(author_meta_file_path, 'w+')

        meta_format_error = 0 
        checked_url_num = 0
        print self.checked_urls
        with open(self.json_file) as fp:
            for line in fp:
                try:
                    article_info = json.loads(line)
                except Exception as e:
                    meta_format_error = meta_format_error + 1
                    continue

                if self.checked_table and not article_info["access_url"] in self.checked_urls:
                    continue
                
                checked_url_num = checked_url_num + 1
                self.convert_to_xml(article_info)

        self.output_meta_file.close()
        self.author_meta_file.close()
        print "meta_format_error :%d" % meta_format_error
        if self.checked_table:
            print "checked num: %d" % checked_url_num

    def convert_from_database(self):
        #sql = "select collection_title from article_info where collection_title like '%cadernos de sa%' limit 1"
        #collection_titles = self.mysql_helper.query_all(sql)
        #for collection_title in collection_titles:
        #    collection_title = collection_title['collection_title'].encode("utf-8")
        #    print collection_title
        #sys.exit(0)
        #article_info_table = "article_info-update"
        article_info_table = "article_info_check"
        author_sql = "select * from article_author"
        authors = self.mysql_helper.query_all(author_sql)
        self.author_map = {}

        for author in authors:
            work_id = author['work_id']

            if work_id not in self.author_map:
                self.author_map[work_id] = [author]
            else:
                self.author_map[work_id].append(author)

        sql = "select * from `%s`" % article_info_table
        articles = self.mysql_helper.query_all(sql)
        for article_info in articles:
            self.convert_to_xml_from_database(article_info)

    def convert_to_xml_from_database(self, article_info):
        source_name_str = self.get_article_field(article_info, "source_name")

        journal_name = self.get_article_field(article_info, "collection_title").encode("utf-8")
        journal_meta = self.all_journal_meta[journal_name.lower()]
        url = self.get_article_field(article_info, "access_url")
        self.url = url
        self.current_url = url
        print "process %s" % url
        volume = self.get_article_field(article_info, "volume").replace("vol.", "").strip()
        issue = self.get_article_field(article_info, "issue").replace("no.", "")

        doi = self.get_article_field(article_info, "doi")
        title = self.get_article_field(article_info, "work_title")
        abstract = self.get_article_field(article_info, "abstract")
        if abstract == "":
            abstract = "cannot no abstract right now, maybe has no abstract or it's too hard to get"
        xlink = self.get_article_field(article_info, "license_url")
        license_text = self.get_article_field(article_info, "license_text")
        copyright_text = self.get_article_field(article_info, "copyright") 
        publish_date  = self.get_article_field(article_info, "publish_date")

        #publish_date比如是2017-12-18这种格式,如果缺少『日』,那么就默认为1
        publish_date_elems = publish_date.replace(" 00:00:00", "").split('-')
        #print "publish_date: %s" % publish_date
        if len(publish_date_elems) == 1:
            pass
        elif len(publish_date_elems) == 2:
            publish_date = publish_date + "-1"
            publish_date = "%s-%02d" % (int(publish_date_elems[0]), int(publish_date_elems[1])) 
        elif len(publish_date_elems) == 3:
            publish_date = "%s-%02d-%02d" % (publish_date_elems[0], int(publish_date_elems[1]), int(publish_date_elems[2]))
        else:
            raise Exception("unexcept publish date format :%s, %s" % (publish_date, self.url))

        pdf_link = self.get_article_field(article_info, "pdf_access_url|pdf_link")
        keywords = self.get_article_field(article_info, "keywords")

        article_id = self.get_article_field(article_info, "work_id")
        collection_id = journal_meta['collection_id']
        if collection_id == "JO201808090000043NK":
            date = "20170523"
            issue_dir = "%s/%s^Y%s^V%s^N%s" % (self.save_file, journal_meta['collection_id'], date, volume, issue)
            issue_dir = issue_dir.replace(";", "_")
            xml_file_path = "%s/%s.xml" % (issue_dir, article_id)
        else:
            issue_dir = self.get_article_field(article_info, "xml_uri")
            issue_dir = os.path.dirname(issue_dir).replace(":", "_")
            xml_file_path = self.get_article_field(article_info, "xml_uri")

        if not os.path.exists(issue_dir):
            os.makedirs(issue_dir)

        pdf_name = self.get_article_field(article_info, "ro_title")
        pdf_file_path = self.get_article_field(article_info, "pdf_uri")
        create_time_text = self.get_article_field(article_info, "create_time")

        #create time必须按照格式来，不然xml校验通过不了
        #print "create time :%s" % create_time_text
        create_time_obj = datetime.datetime.strptime(str(create_time_text), "%Y-%m-%d %H:%M:%S")
        create_time_text = create_time_obj.strftime('%Y-%m-%dT%H:%M:%S')

        creator = self.get_article_field(article_info, "creator")
        collection_id_text = self.get_article_field(article_info, "collection_id")
        source_id_text = self.get_article_field(article_info, "source_id")
        system_id = self.get_article_field(article_info, "system_id")
        ro_id = self.get_article_field(article_info, "ro_id")
        issn = self.get_article_field(article_info, "issn")
        eissn = self.get_article_field(article_info, "eissn")
        platform_url = self.get_article_field(article_info, "platform_url")
        language = self.get_article_field(article_info, "language")
        country_text = self.get_article_field(article_info, "country")
        publish_year_text = self.get_article_field(article_info, "publish_year")

        #2. create xml for this article
        doc = minidom.Document()
        root = doc.createElement('nstl_ors:work_group')
        doc.appendChild(root)
        root.setAttribute("xmlns:nstl", "http://spec.nstl.gov.cn/specification/namespace")
        root.setAttribute("xmlns:nstl_ors", "http://open-resources.nstl.gov.cn/elements/2015")
        root.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink")
        root.setAttribute("xmlns:xml", "http://www.w3.org/XML/1998/namespace")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:schemaLocation", "http://open-resources.nstl.gov.cn/elements/2015")

        work_meta = doc.createElement("nstl_ors:work_meta")
        root.appendChild(work_meta)

        # Add collection meta
        collection_meta = doc.createElement("nstl_ors:collection_meta")
        work_meta.appendChild(collection_meta)
        collection_id = doc.createElement("nstl_ors:collection_id")
        collection_meta.appendChild(collection_id)
        text = doc.createTextNode(collection_id_text)
        collection_id.appendChild(text)
        collection_id_other = doc.createElement("nstl_ors:collection_id_other")
        collection_meta.appendChild(collection_id_other)
        collection_id_other.appendChild(doc.createTextNode(system_id))
        collection_id_other.setAttribute("identifier-type", 'SystemID')
        collection_id_other = doc.createElement("nstl_ors:collection_id_other")
        collection_meta.appendChild(collection_id_other)
        collection_id_other.appendChild(doc.createTextNode(issn))
        collection_id_other.setAttribute("identifier-type", 'ISSN')
        collection_id_other = doc.createElement("nstl_ors:collection_id_other")
        collection_id_other.appendChild(doc.createTextNode(eissn))
        collection_id_other.setAttribute("identifier-type", 'EISSN')
        collection_meta.appendChild(collection_id_other)
        collection_title = doc.createElement("nstl_ors:collection_title")
        collection_title.appendChild(doc.createCDATASection(journal_name))
        collection_meta.appendChild(collection_title)
        collection_publiction_type = doc.createElement("nstl_ors:publication_type")
        collection_publiction_type.appendChild(doc.createTextNode("Journal"))
        collection_meta.appendChild(collection_publiction_type)
        access_group = doc.createElement("nstl_ors:access_group")
        collection_meta.appendChild(access_group)
        access_meta = doc.createElement("nstl_ors:access_meta")
        access_group.appendChild(access_meta)
        access_url = doc.createElement("nstl_ors:access_url")
        access_url.appendChild(doc.createCDATASection(platform_url))
        access_meta.appendChild(access_url)
        source_meta = doc.createElement("nstl_ors:source_meta")
        access_meta.appendChild(source_meta)
        source_id = doc.createElement("nstl_ors:source_id")
        source_meta.appendChild(source_id)
        source_id.appendChild(doc.createTextNode(source_id_text))
        source_name = doc.createElement("nstl_ors:source_name")
        source_meta.appendChild(source_name)
        source_name.appendChild(doc.createCDATASection(source_name_str))
        source_type = doc.createElement("nstl_ors:souce_type")
        source_meta.appendChild(source_type)
        source_type.appendChild(doc.createTextNode("Publisher"))

        work_id = doc.createElement("nstl_ors:work_id")
        work_meta.appendChild(work_id)
        work_id.appendChild(doc.createTextNode(article_id))
        work_id_other = doc.createElement("nstl_ors:work_id_other")
        work_meta.appendChild(work_id_other)
        work_id_other.appendChild(doc.createTextNode(doi))
        work_id_other.setAttribute("identifier-type", "DOI")
        work_title = doc.createElement("nstl_ors:work_title")
        work_meta.appendChild(work_title)
        work_title.appendChild(doc.createCDATASection(title))
        publication_type = doc.createElement("nstl_ors:publication_type")
        work_meta.appendChild(publication_type)
        publication_type.appendChild(doc.createTextNode("JournalArticle"))
        contributer_group = doc.createElement("nstl_ors:contributer_group")
        work_meta.appendChild(contributer_group)
        index = 0

        has_author = True
        if article_id not in self.author_map:
            has_author = False

        author_infos = {}
        if has_author:
            for author in self.author_map[article_id]:
                author_name = author['author_name']
                institution_name = author['institution_name']
            
                if author_name not in author_infos:
                    author_infos[author_name] = [institution_name]
                else:
                    author_infos[author_name].append(institution_name)

        for author, institutions in author_infos.items():
            contributer_meta = doc.createElement("nstl_ors:contributer_meta")
            contributer_group.appendChild(contributer_meta)
            name = doc.createElement("nstl_ors:name")
            contributer_meta.appendChild(name)
            name.appendChild(doc.createCDATASection(author))
            role = doc.createElement("nstl_ors:role")
            contributer_meta.appendChild(role)
            role.appendChild(doc.createTextNode("Author"))
            affiliation = doc.createElement("nstl_ors:affiliation")
            contributer_meta.appendChild(affiliation)
            institution_meta = doc.createElement("nstl_ors:institution-meta")
            affiliation.appendChild(institution_meta)
            for institution in institutions:
                institution_name = doc.createElement("nstl_ors:institution_name")
                institution_meta.appendChild(institution_name)
                institution_name.appendChild(doc.createCDATASection(institution))

        keywords_group = doc.createElement("nstl_ors:kwd-group")
        work_meta.appendChild(keywords_group)
        keywords= keywords.split(";")
        for keyword_txt in keywords:
            if keyword_txt is None:
                keyword_txt = ""
            keyword = doc.createElement("nstl_ors:keyword")
            keywords_group.appendChild(keyword)
            keyword.appendChild(doc.createCDATASection(keyword_txt)) 
        
        language = doc.createElement("nstl_ors:language")
        work_meta.appendChild(language)
        language.appendChild(doc.createTextNode("eng"))

        abstract_node = doc.createElement("nstl_ors:abstract")
        work_meta.appendChild(abstract_node)
        abstract_node.appendChild(doc.createCDATASection(abstract)) 

        country = doc.createElement("nstl_ors:country")
        work_meta.appendChild(country)
        country.appendChild(doc.createTextNode(country_text))

        #TODO页码
        start_page = self.get_article_field(article_info, "start_page");
        end_page = self.get_article_field(article_info, "end_page");
        total_page_number = self.get_article_field(article_info, 'total_page_number');
        if start_page != "" and end_page != "":
            # 有页码才显示页码
            total_page_number_elem = doc.createElement("nstl_ors:total_page_number")
            work_meta.appendChild(total_page_number_elem)
            total_page_number_elem.appendChild(doc.createTextNode(total_page_number))
            start_page_elem = doc.createElement("nstl_ors:start_page")
            work_meta.appendChild(start_page_elem)
            start_page_elem.appendChild(doc.createTextNode(start_page))
            end_page_elem = doc.createElement("nstl_ors:end_page")
            work_meta.appendChild(end_page_elem)
            end_page_elem.appendChild(doc.createTextNode(end_page))

        publication_year = doc.createElement("nstl_ors:publication_year")
        work_meta.appendChild(publication_year)
        publication_year.appendChild(doc.createTextNode(publish_year_text))
        
        volumn_node = doc.createElement("nstl_ors:volume")
        work_meta.appendChild(volumn_node)
        volumn_node.appendChild(doc.createTextNode(volume))

        issue_node = doc.createElement("nstl_ors:issue")
        work_meta.appendChild(issue_node)
        issue_node.appendChild(doc.createTextNode(issue))

        publish_date_node = doc.createElement("nstl_ors:publication_date")
        work_meta.appendChild(publish_date_node)
        publish_date_node.appendChild(doc.createTextNode(publish_date))

        self_url = doc.createElement("nstl_ors:self-uri")
        work_meta.appendChild(self_url)
        self_url.setAttribute("content-type", "XML")
        self_url.setAttribute("xlink:href", xml_file_path)

        self_url1 = doc.createElement("nstl_ors:self-uri")
        work_meta.appendChild(self_url1)
        self_url1.setAttribute("content-type", "PDF")
        self_url1.setAttribute("xlink:href", self.get_article_field(article_info, 'pdf_access_url|pdf_link'));

        access_group = doc.createElement("nstl_ors:access_group")
        work_meta.appendChild(access_group)

        access_meta = doc.createElement("nstl_ors:access_meta")
        access_group.appendChild(access_meta)
        access_url = doc.createElement("nstl_ors:access_url")
        access_meta.appendChild(access_url)
        access_url.appendChild(doc.createCDATASection(url))
        permissions_meta = doc.createElement("nstl_ors:permissions_meta")
        access_meta.appendChild(permissions_meta)
        copyright_statement = doc.createElement("nstl_ors:copyright-statement")
        if copyright_text == "":
            copyright_text = "no copyright"
        permissions_meta.appendChild(copyright_statement)
        copyright_statement.appendChild(doc.createCDATASection(copyright_text))
        license = doc.createElement("nstl_ors:license")
        permissions_meta.appendChild(license)
        #TODO 通过检查的没加这个
        #license.setAttribute("license-type", journal_meta['license_type'])
        license.setAttribute("xlink:href", xlink)
        license.appendChild(doc.createCDATASection(license_text))
        available_time = doc.createElement("nstl_ors:available_time")
        #TODO
        #permissions_meta.appendChild(available_time)
        available_time.appendChild(doc.createTextNode(journal_meta['available_time']))
        oa_type = doc.createElement("nstl_ors:OA-type")
        #permissions_meta.appendChild(oa_type)
        #TODO
        #oa_type.appendChild(doc.createTextNode(journal_meta['oa_type']))

        #TODO what's this?
        related_object_group = doc.createElement("nstl_ors:related_object_group")
        work_meta.appendChild(related_object_group)
        related_object = doc.createElement("nstl_ors:related_object")
        related_object_group.appendChild(related_object)
        ro_id = doc.createElement("nstl_ors:ro_id")
        related_object.appendChild(ro_id)
        #TODO PDF的ID和Article的ID取一样的，其他需求可能不适用
        ro_id.appendChild(doc.createTextNode(pdf_name))
        ro_title = doc.createElement("nstl_ors:ro_title")
        related_object.appendChild(ro_title)
        ro_title.appendChild(doc.createTextNode(pdf_name))
        ro_type = doc.createElement("nstl_ors:ro_type")
        #TODO
        #related_object.appendChild(ro_type)
        ro_type.appendChild(doc.createTextNode("CompleteContent"))
        media_type = doc.createElement("nstl_ors:media_type")
        related_object.appendChild(media_type)
        media_type.appendChild(doc.createTextNode("PDF"))
        ro_self_url = doc.createElement("nstl_ors:self-uri") 
        related_object.appendChild(ro_self_url)
        ro_self_url.setAttribute("content-type", "PDF")
        ro_self_url.setAttribute("xlink:href", pdf_file_path)  
        ro_access_meta = doc.createElement("nstl_ors:access_meta")
        related_object.appendChild(ro_access_meta)
        ro_access_url = doc.createElement("nstl_ors:access_url")
        ro_access_meta.appendChild(ro_access_url)
        ro_access_url.appendChild(doc.createCDATASection(pdf_link))

        management_meta = doc.createElement("nstl_ors:management-meta")
        work_meta.appendChild(management_meta)
        creator = doc.createElement("nstl_ors:creator")
        management_meta.appendChild(creator)
        creator.appendChild(doc.createTextNode("NK"))
        create_time = doc.createElement("nstl_ors:create_time")
        management_meta.appendChild(create_time)
        create_time.appendChild(doc.createTextNode(str(create_time_text)))
        revision_time = doc.createElement("nstl_ors:revision_time")
        #TODO
        #management_meta.appendChild(revision_time)
        revision_time.appendChild(doc.createTextNode(str(create_time_text)))

        #print article_info
        #print "save to :%s" % xml_file_path
        xml_str = doc.toprettyxml(indent="  ").encode('utf-8')
        with open(xml_file_path, "w") as f:
            f.write(xml_str)

    def convert_to_xml(self, article_info):
        url = self.get_article_field(article_info, "access_url")
        self.url = url

        if "journal" in article_info:
            journal_name = article_info["journal"]
        else:
            journal_name = article_info["collection"]

        if type(journal_name) is list:
            journal_name = journal_name[0]
        journal_name = journal_name.replace("Subscribe to our newsletter", "").replace("GÃ©neros - ", "")\
            .replace("welcomes submissions that encourage scholarly exchange between family medicine and primary health care researchers and practitioners across Africa and the developing world, whilst providing a context", "").strip()
        journal_name = unidecode(journal_name)
        journal_not_found = False
        if journal_name != "":
          if (journal_name.lower() not in self.all_journal_meta):
              if journal_name.upper() in self.journal_name_map:
                  converted_journal_name = self.journal_name_map[journal_name.upper()]
                  if converted_journal_name.lower() not in self.all_journal_meta:
                      print "cannot find meta info for converted_journal_name journal: %s, origin journal: %s" \
                        % (converted_journal_name.lower(), journal_name.upper())
                      #print self.all_journal_meta
                      #sys.exit(0)
                      journal_not_found = True
                  else:
                      journal_name = converted_journal_name
              else:
                  print "journal not in converted journal name map :%s" % (journal_name)
                  journal_not_found = True
        else:
          journal_not_found = True

        if journal_name == "" and journal_not_found:
          #元数据里面没有journal_name，并且journal name和excel不一致
          #那么从excel表里面获取
          self.use_new_journal = use_new_journal
          domain_url = self._get_domain_url(url)
          if domain_url in self.journal_url_to_name:
            journal_name = self.journal_url_to_name[domain_url]
          else:
            print "can not get journal from either meta info or xls, domain:%s, url: %s" % (domain_url, url)
            #raise Exception("can not get journal from either meta info or xls, domain:%s, url: %s" % (domain_url, url))
          
        #过滤太老的article
        try:
            date = self.get_article_field(article_info, "release_year", throw_exception = False).replace(")", "")
        except Exception  as e:
            print "date is empty: %s" % self.url
            return

        if date == "":
            print "date is empty: %s" % url
            return

        min_date = 2005
        if self.use_new_journal:
            min_date = 2005

        if (int(date) < min_date):
            print "too old issue: %s" % date
            return
            
        if journal_not_found:
            #raise Exception("cannot find meta info for journal: %s" % journal_name)
            #print "cannot find meta info for journal: %s,%s" % (journal_name, url)
            print "cannot find meta info for journal: %s, url :%s" % (journal_name.encode('utf-8'), url)
            return
            
        journal_meta = self.all_journal_meta[journal_name.lower()]

        source_name_str = journal_meta['source_name']

        volume = self.get_article_field(article_info, "volume").replace("vol.", "").strip()
        issue = self.get_article_field(article_info, "issue").replace("no.", "")
        #legex_issue = re.compile(r"[\d-]+") //issue也可以不是数字,issue也可以是空
        #if volume == "": #or not legex_issue.match(issue): 
        #    print "invalid volume and issue(%s, %s): %s" % (volume, issue, self.url)
        #    return
        doi = self.get_article_field(article_info, "doi", throw_exception = False) #doi为空..
        doi = doi.replace("http://dx.doi.org/", "")
        title = self.get_article_field(article_info, "title")
        abstract = self.get_article_field(article_info, "abstract", throw_exception = False).replace("View Full-Text", "").strip()
        if abstract == "":
            abstract = "cannot no abstract right now, maybe has no abstract or it's too hard to get"
            #print "abstract is empty: %s" % self.url
            #return

        xlink = self.get_article_field(article_info, "xlink", throw_exception = False)
        if xlink == "":
            xlink = "https://creativecommons.org/licenses/by/4.0/"
        license_text = self.get_article_field(article_info, "license", throw_exception = False)
        if license_text == "":
            license_text = "This is an open access article distributed under the Creative Commons Attribution License which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited. (CC BY 4.0)."
        copyright_text = self.get_article_field(article_info, "copyright", throw_exception = False)
        self.current_url = url

        #Anthor journal publish date may not like "18 August 2017"
        publish_date  = self.get_article_field(article_info, "release_date", throw_exception = False)
        if publish_date == "":
            if "release_year" in article_info:
                publish_date = "%s-01-01" % article_info["release_year"]
            else:
                raise Exception("cannot get release_date from article_info")
        #try:
        #    publish_date = datetime.datetime.strptime(publish_date, "%d %B %Y").strftime("%Y-%m-%d")
        #except Exception as e:
        #    #print "publish date unexpected %s, url is %s" % (publish_date, url)
        #    #return
        #    publish_date = "no publish date"
            
            

        pdf_link = self.get_article_field(article_info, "pdf_link|pdf_url", throw_exception = False)
        if pdf_link == "":
            print "cannot find pdf_link: %s" % self.url
            return

        keywords = self.get_article_field(article_info, "keywords", False, throw_exception = False)
        if (keywords == ""):
            #print "cannot find keywords: %s" % self.url
            keywords = []

        try:
            authors = self.get_article_field(article_info, "author", False, throw_exception = False)
            if authors == "":
                authors = []
            try:
              author_affiliation = self.get_article_field(article_info, "author_affiliation", False)
              if len(author_affiliation) == 0:
                author_affiliation = ["unkonwn"] * len(authors) #可能没有作者机构
            except Exception as e:
              author_affiliation = ["unkonwn"] * len(authors) #可能没有作者机构

            author_affiliation = filter(lambda x: self.filter_author_affiliation(x), author_affiliation)
            if "author_sup" in article_info:
                author_sup = self.get_article_field(article_info, "author_sup", False)
                author_sup = self.format_author_sup(len(authors), author_sup)
            else:
                #如果没有author_sup这个字段，说明作者作何机构是一一对应的,生成一个假的author_sup
                #已知有以下几种情况：
                #a:author_affiliation数目不为1，此时，authors 和 author_affiliation的size应该一样
                #b:author_affiliation数目为1，那么所有的作者都属于这个机构
                author_sup = range(1, len(authors) + 1)
                if len(authors) != len(author_affiliation):
                    if len(author_affiliation) == 1:
                        author_sup = [0] * len(authors)
                    else:
                        print("url %s, size of authors(%d) and author_affiliation(%d) should be equal when author_sup not set!"\
                            % (self.url, len(authors), len(author_affiliation)))
                        return
            if len(authors) != len(author_sup):
                #20180909: authors和author_sup长度不一致时，截断其中一个。懒得重爬了。
                if len(authors) > len(author_sup):
                    authors = authors[:len(author_sup) - 1]
                else:
                    author_sup = author_sup[:len(authors) - 1]
                #print "authors and authos_sup len not equal, This not gonna happen: %s" % url
            
            #if len(author_sup) < 1:
            #    print "no author, not gonna happen :%s" % url
            #    return

        except Exception as e:
            print "author_affiliation fail :%s, reson %s" % (self.url, e.message)
            return
        
        output_meta = {}

        if source_name_str == "Scielo":
            url_pattern = re.compile(r".*script=.*&pid=S.{4}\-.{4}(?P<date>\d{4}).{9}&lng=.*")
            m = url_pattern.match(url)
            if m is None:
                raise Exception("url not match pattern :%s" % url)

            date = m.group('date')

        #1. create issue dir
        issue_dir = "%s/%s^Y%s^V%s^N%s" % (self.save_file, journal_meta['collection_id'], date, volume, issue)
        issue_dir = issue_dir.replace(";", "_")
        if not os.path.exists(issue_dir):
            os.makedirs(issue_dir)

        article_id = self.generate_article_id()
        pdf_name = article_id.replace("JA", "RO")
        xml_file_path = "%s/%s.xml" % (issue_dir, article_id)
        pdf_file_path = "Files/%s.pdf" % pdf_name

        #2. create xml for this article
        doc = minidom.Document()
        root = doc.createElement('nstl_ors:work_group')
        doc.appendChild(root)
        root.setAttribute("xmlns:nstl", "http://spec.nstl.gov.cn/specification/namespace")
        root.setAttribute("xmlns:nstl_ors", "http://open-resources.nstl.gov.cn/elements/2015")
        root.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink")
        root.setAttribute("xmlns:xml", "http://www.w3.org/XML/1998/namespace")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:schemaLocation", "http://open-resources.nstl.gov.cn/elements/2015")

        work_meta = doc.createElement("nstl_ors:work_meta")
        root.appendChild(work_meta)

        # Add collection meta
        collection_meta = doc.createElement("nstl_ors:collection_meta")
        work_meta.appendChild(collection_meta)
        collection_id = doc.createElement("nstl_ors:collection_id")
        collection_meta.appendChild(collection_id)
        try:
            text = doc.createTextNode(journal_meta['collection_id'])
        except Exception:
            print "no collection id journal, url %s" % self.url
            return
        collection_id.appendChild(text)
        collection_id_other = doc.createElement("nstl_ors:collection_id_other")
        collection_meta.appendChild(collection_id_other)
        collection_id_other.appendChild(doc.createTextNode(journal_meta['system_id']))
        collection_id_other.setAttribute("identifier-type", 'SystemID')
        collection_id_other = doc.createElement("nstl_ors:collection_id_other")
        collection_meta.appendChild(collection_id_other)
        collection_id_other.appendChild(doc.createTextNode(journal_meta['issn']))
        collection_id_other.setAttribute("identifier-type", 'ISSN')
        collection_id_other = doc.createElement("nstl_ors:collection_id_other")
        collection_id_other.appendChild(doc.createTextNode(journal_meta['eissn']))
        collection_id_other.setAttribute("identifier-type", 'EISSN')
        collection_meta.appendChild(collection_id_other)
        collection_title = doc.createElement("nstl_ors:collection_title")
        collection_title.appendChild(doc.createCDATASection(journal_name))
        collection_meta.appendChild(collection_title)
        collection_publiction_type = doc.createElement("nstl_ors:publication_type")
        collection_publiction_type.appendChild(doc.createTextNode("Journal"))
        collection_meta.appendChild(collection_publiction_type)
        access_group = doc.createElement("nstl_ors:access_group")
        collection_meta.appendChild(access_group)
        access_meta = doc.createElement("nstl_ors:access_meta")
        access_group.appendChild(access_meta)
        access_url = doc.createElement("nstl_ors:access_url")
        access_url.appendChild(doc.createCDATASection(journal_meta['platform_url']))
        access_meta.appendChild(access_url)
        source_meta = doc.createElement("nstl_ors:source_meta")
        access_meta.appendChild(source_meta)
        source_id = doc.createElement("nstl_ors:source_id")
        source_meta.appendChild(source_id)
        #TODO JOURNAL的Source ID需要拿到
        source_id.appendChild(doc.createTextNode(journal_meta['source_id']))
        if (journal_meta['source_id'].strip() == ''):
            raise Exception("source id is empty: %s" % journal_name);
            
        source_name = doc.createElement("nstl_ors:source_name")
        source_meta.appendChild(source_name)
        source_name.appendChild(doc.createCDATASection(source_name_str))
        source_type = doc.createElement("nstl_ors:souce_type")
        source_meta.appendChild(source_type)
        source_type.appendChild(doc.createTextNode("Publisher"))

        work_id = doc.createElement("nstl_ors:work_id")
        work_meta.appendChild(work_id)
        work_id.appendChild(doc.createTextNode(article_id))
        work_id_other = doc.createElement("nstl_ors:work_id_other")
        work_meta.appendChild(work_id_other)
        work_id_other.appendChild(doc.createTextNode(doi))
        work_id_other.setAttribute("identifier-type", "DOI")
        work_title = doc.createElement("nstl_ors:work_title")
        work_meta.appendChild(work_title)
        work_title.appendChild(doc.createCDATASection(title))
        publication_type = doc.createElement("nstl_ors:publication_type")
        work_meta.appendChild(publication_type)
        publication_type.appendChild(doc.createTextNode("JournalArticle"))
        contributer_group = doc.createElement("nstl_ors:contributer_group")
        work_meta.appendChild(contributer_group)
        index = 0
        for author in authors:
            contributer_meta = doc.createElement("nstl_ors:contributer_meta")
            contributer_group.appendChild(contributer_meta)
            #TODO 通过检查的xml没有加这个属性
            name = doc.createElement("nstl_ors:name")
            contributer_meta.appendChild(name)
            name.appendChild(doc.createCDATASection(author))
            role = doc.createElement("nstl_ors:role")
            contributer_meta.appendChild(role)
            role.appendChild(doc.createTextNode("Author"))
            affiliation = doc.createElement("nstl_ors:affiliation")
            contributer_meta.appendChild(affiliation)
            affiliation_index = str(author_sup[index])
            institution_meta = doc.createElement("nstl_ors:institution-meta")
            affiliation.appendChild(institution_meta)
            for aff_index in affiliation_index.split(','):
                institution_name = doc.createElement("nstl_ors:institution_name")
                institution_meta.appendChild(institution_name)
                try:
                    institution_name.appendChild(doc.createCDATASection(author_affiliation[int(aff_index)-1]))
                except Exception as e:
                    print "catch exception when add authori %s" % url
                    #print article_info
                    #raise Exception("catch exception when add author")
                    return
                author_meta = {}
                author_meta['work_id'] = article_id
                author_meta['author_name'] = author
                author_meta['institution_name'] = author_affiliation[int(aff_index)-1]
                self.save_article_author_info(author_meta)
                #self.author_meta_file.write("%s@@%s@@%s"%(article_id, author.encode('utf-8'), author_affiliation[int(aff_index)-1].encode('utf-8')))
                #self.author_meta_file.write('\n')
           

            #TODO 通过检查的xml，作者的标注不一样
            #xref = doc.createElement("nstl_ors:xref")
            #contributer_meta.appendChild(xref)
            #xref.setAttribute("ref-type", "institution-meta")
            #affiliation_index = author_sup[index]
            #affiliation_index = ','.join(['I'+ k for k in affiliation_index.split(',')])
            #xref.setAttribute("rid", affiliation_index)
            #index = index + 1

        #TODO 通过检查的xml，作者的标注还不一样
        #institution_group = doc.createElement("nstl_ors:institution_group")
        #work_meta.appendChild(institution_group)
        #institution_index = 0
        #for affliation in author_affiliation:
        #    institution_meta = doc.createElement("nstl_ors:institution-meta")
        #    institution_group.appendChild(institution_meta)
        #    institution_meta.setAttribute("inst_id", 'I' + str(institution_index + 1))
        #    
        #    institution_name = doc.createElement("nstl_ors:institution_name")
        #    institution_meta.appendChild(institution_name)
        #    institution_name.appendChild(doc.createCDATASection(author_affiliation[institution_index]))
        #    institution_index = institution_index + 1

        keywords_group = doc.createElement("nstl_ors:kwd-group")
        work_meta.appendChild(keywords_group)
        for keyword_txt in keywords:
            if keyword_txt is None:
                keyword_txt = ""
            keyword = doc.createElement("nstl_ors:keyword")
            keywords_group.appendChild(keyword)
            keyword.appendChild(doc.createCDATASection(keyword_txt)) 
        
        language = doc.createElement("nstl_ors:language")
        work_meta.appendChild(language)
        language.appendChild(doc.createTextNode("eng"))

        abstract_node = doc.createElement("nstl_ors:abstract")
        work_meta.appendChild(abstract_node)
        abstract_node.appendChild(doc.createCDATASection(abstract)) 

        country = doc.createElement("nstl_ors:country")
        work_meta.appendChild(country)
        country.appendChild(doc.createTextNode(journal_meta['country']))

        #TODO页码
        end_page = self.get_article_field(article_info, "lpage");
        start_page = self.get_article_field(article_info, "fpage");
        total_page_number = '';
        if start_page != "" and end_page != "":
            # 有页码才显示页码
            total_page_number = str(int(end_page) - int(start_page) + 1);
            total_page_number_elem = doc.createElement("nstl_ors:total_page_number")
            work_meta.appendChild(total_page_number_elem)
            total_page_number_elem.appendChild(doc.createTextNode(total_page_number))
            start_page_elem = doc.createElement("nstl_ors:start_page")
            work_meta.appendChild(start_page_elem)
            start_page_elem.appendChild(doc.createTextNode(start_page))
            end_page_elem = doc.createElement("nstl_ors:end_page")
            work_meta.appendChild(end_page_elem)
            end_page_elem.appendChild(doc.createTextNode(end_page))

        publication_year = doc.createElement("nstl_ors:publication_year")
        work_meta.appendChild(publication_year)
        publication_year.appendChild(doc.createTextNode(date))
        
        volumn_node = doc.createElement("nstl_ors:volume")
        work_meta.appendChild(volumn_node)
        volumn_node.appendChild(doc.createTextNode(volume))

        issue_node = doc.createElement("nstl_ors:issue")
        work_meta.appendChild(issue_node)
        issue_node.appendChild(doc.createTextNode(issue))

        publish_date_node = doc.createElement("nstl_ors:publication_date")
        work_meta.appendChild(publish_date_node)
        publish_date_node.appendChild(doc.createTextNode(publish_date))

        self_url = doc.createElement("nstl_ors:self-uri")
        work_meta.appendChild(self_url)
        self_url.setAttribute("content-type", "XML")
        self_url.setAttribute("xlink:href", xml_file_path)

        self_url1 = doc.createElement("nstl_ors:self-uri")
        work_meta.appendChild(self_url1)
        self_url1.setAttribute("content-type", "PDF")
        self_url1.setAttribute("xlink:href", self.get_article_field(article_info, 'pdf_access_url|pdf_link'));

        access_group = doc.createElement("nstl_ors:access_group")
        work_meta.appendChild(access_group)

        access_meta = doc.createElement("nstl_ors:access_meta")
        access_group.appendChild(access_meta)
        access_url = doc.createElement("nstl_ors:access_url")
        access_meta.appendChild(access_url)
        access_url.appendChild(doc.createCDATASection(url))
        permissions_meta = doc.createElement("nstl_ors:permissions_meta")
        access_meta.appendChild(permissions_meta)
        copyright_statement = doc.createElement("nstl_ors:copyright-statement")
        if copyright_text == "":
            copyright_text = "no copyright"
        permissions_meta.appendChild(copyright_statement)
        copyright_statement.appendChild(doc.createCDATASection(copyright_text))
        license = doc.createElement("nstl_ors:license")
        permissions_meta.appendChild(license)
        #TODO 通过检查的没加这个
        #license.setAttribute("license-type", journal_meta['license_type'])
        license.setAttribute("xlink:href", xlink)
        license.appendChild(doc.createCDATASection(license_text))
        available_time = doc.createElement("nstl_ors:available_time")
        #TODO
        #permissions_meta.appendChild(available_time)
        available_time.appendChild(doc.createTextNode(journal_meta['available_time']))
        oa_type = doc.createElement("nstl_ors:OA-type")
        #permissions_meta.appendChild(oa_type)
        #TODO
        #oa_type.appendChild(doc.createTextNode(journal_meta['oa_type']))

        #TODO what's this?
        related_object_group = doc.createElement("nstl_ors:related_object_group")
        work_meta.appendChild(related_object_group)
        related_object = doc.createElement("nstl_ors:related_object")
        related_object_group.appendChild(related_object)
        ro_id = doc.createElement("nstl_ors:ro_id")
        related_object.appendChild(ro_id)
        #TODO PDF的ID和Article的ID取一样的，其他需求可能不适用
        ro_id.appendChild(doc.createTextNode(pdf_name))
        ro_title = doc.createElement("nstl_ors:ro_title")
        related_object.appendChild(ro_title)
        ro_title.appendChild(doc.createTextNode(pdf_name + ".pdf"))
        ro_type = doc.createElement("nstl_ors:ro_type")
        #TODO
        #related_object.appendChild(ro_type)
        ro_type.appendChild(doc.createTextNode("CompleteContent"))
        media_type = doc.createElement("nstl_ors:media_type")
        related_object.appendChild(media_type)
        media_type.appendChild(doc.createTextNode("PDF"))
        ro_self_url = doc.createElement("nstl_ors:self-uri") 
        related_object.appendChild(ro_self_url)
        ro_self_url.setAttribute("content-type", "PDF")
        ro_self_url.setAttribute("xlink:href", pdf_file_path)  
        ro_access_meta = doc.createElement("nstl_ors:access_meta")
        related_object.appendChild(ro_access_meta)
        ro_access_url = doc.createElement("nstl_ors:access_url")
        ro_access_meta.appendChild(ro_access_url)
        ro_access_url.appendChild(doc.createCDATASection(pdf_link))

        management_meta = doc.createElement("nstl_ors:management-meta")
        work_meta.appendChild(management_meta)
        creator = doc.createElement("nstl_ors:creator")
        management_meta.appendChild(creator)
        creator.appendChild(doc.createTextNode("NK"))
        create_time = doc.createElement("nstl_ors:create_time")
        management_meta.appendChild(create_time)
        create_time.appendChild(doc.createTextNode("%s" % self.now))
        revision_time = doc.createElement("nstl_ors:revision_time")
        #TODO
        #management_meta.appendChild(revision_time)
        revision_time.appendChild(doc.createTextNode("%s" % self.now))

        xml_str = doc.toprettyxml(indent="  ").encode('utf-8')
        with open(xml_file_path, "w") as f:
            f.write(xml_str)

        pdf_dir = "C:\Users\hp\Desktop\%s" % pdf_file_path.replace("/", "\\").replace(".\\xml_result\\", "xml_result")

        #print "%s,%s,%s" %(pdf_dir, pdf_link, doi)
        output_meta['collection_id'] = journal_meta['collection_id'] #期刊ID
        output_meta['source_id'] = journal_meta['source_id'] #平台ID
        output_meta['system_id'] = journal_meta['system_id'] #加工号?
        output_meta['ro_id'] = pdf_name
        output_meta['work_id'] = article_id
        output_meta['doi'] = doi
        output_meta['work_title'] = title
        output_meta['issn'] = journal_meta['issn']
        output_meta['eissn'] = journal_meta['eissn']
        output_meta['collection_title'] = journal_name
        output_meta['platform_url'] = journal_meta['platform_url']
        output_meta['source_name'] = source_name_str
        output_meta['keywords'] = ";".join(keywords)
        output_meta['language'] = 'eng'
        output_meta['abstract'] = abstract
        output_meta['country'] = journal_meta['country']
        output_meta['publish_year'] = date
        output_meta['publish_date'] = publish_date
        output_meta['volume'] = volume
        output_meta['issue'] = issue
        output_meta['access_url'] = url
        output_meta['license_text'] = license_text
        output_meta['license_url'] = xlink
        output_meta['copyright'] = copyright_text
        output_meta['ro_title'] = pdf_name + ".pdf"
        output_meta['xml_uri'] = xml_file_path
        output_meta['pdf_uri'] = pdf_file_path
        output_meta['pdf_access_url'] = pdf_link
        output_meta['creator'] = 'NK'
        output_meta['create_time'] = self.now
        output_meta['start_page'] = start_page
        output_meta['end_page'] = end_page
        output_meta['total_page_number'] = total_page_number
        self.save_article_info(output_meta)
        #self.output_meta_file.write(json.dumps(output_meta))
        #self.output_meta_file.write('\n')

    """
    Save article info to mysql, update when row exists
    """
    def save_article_info(self, article_info):
        self.mysql_helper.insert(self.article_table, article_info)
    """
    Save article author info to mysql, update when row exists
    """
    def save_article_author_info(self, article_author_info):
        self.mysql_helper.insert(self.author_table, article_author_info)

    def _get_domain_url(self, url):
      try:
        journal_url = urlparse.urljoin(url, '/').replace("https", "http")
        url = urlparse.urljoin(url, '/').replace("https", "http").replace("www.", "")
        return url
      except Exception:
        return ""

    def load_journal_meta(self, all_journal_meta_xls):
        """
        Load all journal meta info from xls file
        """
        data = xlrd.open_workbook(all_journal_meta_xls)

        #TODO 其他需求journal元数据表可能不是这样
        if not self.use_new_journal:
            table = data.sheets()[0] #3rd sheet is main sheet
        else:
            table = data.sheets()[0]
        nrows = table.nrows
        ncols = table.ncols
        for i in xrange(0,nrows):
            if not self.use_new_journal:
                #TODO 第一行没用，其他需求可能不适用
                if (i < 1):
                    continue

            rowValues= table.row_values(i)

            if not self.use_new_journal:
                journal = unidecode(rowValues[6].lower().strip())
                if journal in self.all_journal_meta:
                   raise Exception("journal find multiple meta info: %s" % journal)

                print "add journal: %s" % journal
                if journal == "":
                    continue
                self.all_journal_meta[journal] = {
                'journal_id': rowValues[0],
                'issn': rowValues[8],
                'eissn': rowValues[9],
                'country': rowValues[10],
                'language': rowValues[11], 'license_type': rowValues[25], 'license_text': rowValues[26], 'oa_type': rowValues[32], 
                'available_time': rowValues[33],
                'platform_url': rowValues[29], 'source_name': rowValues[28], 'system_id': rowValues[4],
                'collection_id': rowValues[1], 'source_id': rowValues[2]}
                journal_url = self._get_domain_url(rowValues[31])
            else:
                #后面OA新增的期刊，excel格式不一样
                journal = rowValues[4].lower().strip()
                if journal == "":
                    break;
                if journal in self.all_journal_meta:
                   raise Exception("journal find multiple meta info: %s" % journal)

                self.all_journal_meta[journal] = {
                'issn': rowValues[5],
                'eissn': rowValues[6],
                'country': rowValues[9],
                'language': rowValues[7], 'license_type': rowValues[12], 'license_text': '', 'oa_type': rowValues[18], 
                'available_time': rowValues[22],
                'platform_url': rowValues[15], 'source_name': rowValues[14], 'system_id': rowValues[3],
                'collection_id': rowValues[32], 'source_id': rowValues[33]}
                journal_url = self._get_domain_url(rowValues[17])

            self.journal_url_to_name[journal_url] = journal

    def get_journal_id(self, journal_name):
        """
        Generate journal_id, for example:JO201709240000001NK
        """
        if journal_name in self.journal_ids:
            return self.journal_ids[journal_name]

        journal_id = "JO%s%07dNK" % (self.today, self.all_journal_meta[journal_name.lower()]['journal_id'])
        self.journal_ids[journal_name] = journal_id
        return journal_id

    def filter_author_affiliation(self, author_affiliation):
        not_affiliations = ['These authors contributed equally to this work.', 'Author to whom correspondence should be addressed.']

        for not_affiliation in not_affiliations:
            if not_affiliation in author_affiliation.strip():
                return False

        return True

    def format_author_sup(self, author_size, author_sup, supplement = True):
        """
        Filter some invalid author sup, and supplement author sup if need
        For example: author_size is 3, author_sup is ["1,2,", "*"], will return
        ["1,2", "1", "1"]
        """
        if type(author_sup) is not list:
            #may not extract author sup
            author_sup = []

        index = 0
        while(index < len(author_sup)):
            sup_list = author_sup[index].split(',')
            sup_list = [k for k in sup_list if k.isdigit()]
            if len(sup_list) == 0:
                sup_list = ['1']
            author_sup[index] = ",".join(sup_list)
            index = index + 1
        
        if supplement:
            fill_index = len(author_sup)
            while fill_index <= author_size -1:
                author_sup.append('1')
                fill_index = fill_index + 1

        return author_sup

    def generate_article_id(self):
        """
        Generate article id, for example:JA201709240000001NK
        """
        article_id = "JA%s%07dNK" % (self.today, self.next_article_id)
        self.next_article_id = self.next_article_id + 1
        return article_id

    def get_article_field(self, article_info, field, convert = True, throw_exception = False):
        fields = field.split("|")
        ret = ""
        for field in fields:
            ret = self.get_article_field_inner(article_info, field, convert, throw_exception)
            if ret != "":
                break
        return ret

    def get_article_field_inner(self, article_info, field, convert = True, throw_exception = True):
        if field not in article_info:
            if throw_exception:
                raise Exception ("field %s is empty, url is :%s" % (field, self.url))
            else:
                ret =  ""
        elif type(article_info[field]) is list:
            if convert:
                ret =  ",".join(filter(None, article_info[field]))
            else:
                ret =  article_info[field]
        else:
            ret = article_info[field]

        try:
            ret = ret.decode('latin1')
        except Exception as e:
            pass

        if ret is None:
            ret = ""
        return ret

if __name__ == "__main__":
    use_new_journal = False
    if len(sys.argv) == 4:
        journal_meta = sys.argv[1]
        input_filename = sys.argv[2]
        save_path = sys.argv[3]
        table_suffix = None
        checked_table = None
    elif len(sys.argv) == 5:
        journal_meta = sys.argv[1]
        input_filename = sys.argv[2]
        save_path = sys.argv[3]
        table_suffix = sys.argv[4]
        checked_table = None
    elif len(sys.argv) == 6:
        journal_meta = sys.argv[1]
        input_filename = sys.argv[2]
        save_path = sys.argv[3]
        table_suffix = sys.argv[4]
        checked_table = sys.argv[5]
    else:
        print "Usage: python json2xml.py jounal_meta input_filename save_path [table_suffix] [checked_table]"
        sys.exit(1)
        
    json2xml = Json2Xml(journal_meta, input_filename, save_path, table_suffix = table_suffix, use_new_journal = use_new_journal, checked_table = checked_table)
    json2xml.convert()
    #json2xml.convert_from_database()
