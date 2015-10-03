# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
import os


class SkillportSpider(scrapy.Spider):
    name = "skillport"
    allowed_domains = ["mobile.skillport.books24x7.com", "secure.books24x7.com"]

    login_url = 'https://secure.books24x7.com/express/login.asp'

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
                                   callback=self.logged_in,
                                   headers={'Referer':'http://mobile.skillport.books24x7.com/login.asp'}
                               )]

    def logged_in(self, response):
        self.logger.info("logged into skillport")
        with open("login.html", 'wb') as f:
            f.write(response.body)

        first_page_url = 'http://mobile.skillport.books24x7.com/viewer.asp?bookid=88814&chunkid=0000000001'
        yield scrapy.Request(first_page_url, callback=self.parse_page)

    def parse_page(self, response):
        self.logger.info("jest i strona")
        with open("page.html", 'wb') as f:
            f.write(response.body)
        return None
