# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
import os


class SkillportSpider(scrapy.Spider):
    name = "skillport"
    allowed_domains = ["mobile.skillport.books24x7.com", "secure.books24x7.com"]
    start_urls = (
        'http://mobile.skillport.books24x7.com/login.asp',
        #'http://mobile.skillport.books24x7.com/viewer.asp?bookid=88814',
    )

    def parse(self, response):
        return scrapy.FormRequest.from_response(response,
                                                formname="loginform",
                                                formdata={
                                                    "usr": os.environ["SS2BOOK_USERNAME"],
                                                    "pwd": os.environ["SS2BOOK_PASSWORD"],
                                                    "gc": os.environ["SS2BOOK_GROUPCODE"]
                                                },
                                                callback=self.logged_in)

    def logged_in(self, response):
        self.logger.info("logged into skillport")
        with open("login.html", 'wb') as f:
            f.write(response.body)
        r = response.request
        r.replace('http://mobile.skillport.books24x7.com/viewer.asp?bookid=88814')
        return r

    def page(self, response):
        self.logger.info("jest i strona")
        with open("page.html", 'wb') as f:
            f.write(response.body)
        return None
