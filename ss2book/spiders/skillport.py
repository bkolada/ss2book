# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
import os
from ss2book import settings
import re


class SkillportSpider(scrapy.Spider):
    name = "skillport"
    allowed_domains = ["mobile.skillport.books24x7.com", "secure.books24x7.com"]
    login_url = 'https://secure.books24x7.com/express/login.asp'

    def __init__(self, book_id="88814", *args, **kwargs):
        super(SkillportSpider, self).__init__(*args, **kwargs)
        self.book_id = book_id
        directory_path = os.path.join(settings.TMP_DIR, self.book_id)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

    def save_response(self, response, filename):
        file_path = os.path.join(settings.TMP_DIR, self.book_id, filename)
        self.logger.debug("saving response from %s to %s" % (response.url, file_path))
        with open(file_path, "wb") as f:
            f.write(response.body)

    def start_requests(self):
        # post data:
        # usr=username&pwd=password&gc=group_code&mc=1&ic=1&nojs=1&task=dologin&retpage=login.asp&app=skillport
        form = {
            "usr": os.environ["SS2BOOK_USERNAME"],
            "pwd": os.environ["SS2BOOK_PASSWORD"],
            "gc": os.environ["SS2BOOK_GROUPCODE"],
            "mc": "1",
            "ic": "1",
            "nojs": "1",
            "task": "dologin",
            "retpage": "login.asp",
            "app": "skillport"
        }
        return [scrapy.FormRequest(self.login_url,
                                   formdata=form,
                                   callback=self.parse_login,
                                   headers={'Referer': 'http://mobile.skillport.books24x7.com/login.asp'}
                               )]

    def parse_login(self, response):
        """
        parse login response

        @url file:///tmp/ss2book/invalid_username_password.html
        @returns items 0 0
        @returns request 0 0
        """
        self.save_response(response, "confirm_log_in.html")
        if 'logout' in response.body.lower():
            self.logger.info("logged into skillport")
            first_page_url = 'http://mobile.skillport.books24x7.com/viewer.asp?bookid=%s&chunkid=0000000001' % self.book_id
            yield scrapy.Request(first_page_url, callback=self.parse_page, meta={'page_num':1})
        else:
            self.logger.critical("Crawler couldn't log into skillport. Crawling aborted")

    def parse_page(self, response):
        """
        parse page response

        @url file:///tmp/ss2book/first_page.html
        @returns items 0 0
        @returns request 1 1
        """
        if '<A HREF="help.asp?item=membership" BORDER="0">offlined</A>'.lower() in response.body.lower():
            self.logger.critical("Crawler couldn't get page - content is scrambled. Crawling aborted")
            return

        page_num = response.meta.get('page_num', -1)
        self.logger.info("got page")
        self.save_response(response, "page%d.html" % page_num)

        next_chunk = self.gen_next_chunk(response.body)
        if next_chunk == "00000000-1":
            self.logger.info("Crawler finished a book. Thank you")
            return

        next_page_url = 'http://mobile.skillport.books24x7.com/viewer.asp?bookid=%s&chunkid=%s' % (self.book_id, next_chunk)
        yield scrapy.Request(next_page_url, callback=self.parse_page, meta={'page_num':page_num+1} if page_num != -1 else {})

    def gen_next_chunk(self, body):
        cm_pattern = "var cm = new Array\((.*?)\)"
        cm_payload = [i if len(i) == 2 else '0'+i for i in re.findall(cm_pattern, body)[-1].split(',')]
        self.logger.debug("cm_payload: %s", cm_payload)

        ax_pattern = "var a(1|2|3|4|5) = new Array\(\d+,(\d+),\d+\)"
        ax_list = re.findall(ax_pattern, body)[-5:]
        self.logger.debug("ax_list: %s", ax_list)

        result = ''.join([ cm_payload[int(value)] for _x, value in ax_list])
        self.logger.debug("next_chunk: %s", result)

        return result
