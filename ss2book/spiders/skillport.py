# -*- coding: utf-8 -*-
import scrapy
import os
from ss2book import settings
import re


class SkillportSpider(scrapy.Spider):
    name = 'skillport'
    allowed_domains = ['mobile.skillport.books24x7.com', 'secure.books24x7.com']
    login_url = 'https://secure.books24x7.com/express/login.asp'
    mobile_login_url = 'http://mobile.skillport.books24x7.com/login.asp'
    page_url = 'http://mobile.skillport.books24x7.com/viewer.asp?bookid=%s&chunkid=%s'
    logout_url = 'http://mobile.skillport.books24x7.com/abandonsession.asp'

    def __init__(self, book_id='62126', *args, **kwargs):
        super(SkillportSpider, self).__init__(*args, **kwargs)
        self.book_id = book_id
        self.directory_path = os.path.join(settings.TMP_DIR, self.book_id)
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

    def start_requests(self):
        form = {
            'usr': os.environ['SS2BOOK_USERNAME'],
            'pwd': os.environ['SS2BOOK_PASSWORD'],
            'gc': os.environ['SS2BOOK_GROUPCODE'],
            'mc': '1',
            'ic': '1',
            'nojs': '1',
            'task': 'dologin',
            'retpage': 'login.asp',
            'app': 'skillport'
        }
        self.logger.info(form)
        return [scrapy.FormRequest(self.login_url,
                                   formdata=form,
                                   callback=self.parse_login,
                                   headers={'Referer': self.mobile_login_url}
                                   )]

    def parse_login(self, response):
        """
        parse login response

        @url file:///tmp/ss2book/invalid_username_password.html
        @returns items 0 0
        @returns request 0 0
        """
        self.save_response(response, "login.html")
        if 'abandonsession.asp' in response.body:
            self.logger.info("logged into skillport")
            first_page_url = self.page_url % (self.book_id, '0000000001')
            yield scrapy.Request(first_page_url, callback=self.parse_page, meta={'page_num': 1})
        else:
            self.logger.critical("Crawler couldn't log into skillport. Crawling aborted")

    def parse_page(self, response):
        """
        parse page response

        @url file:///tmp/ss2book/first_page.html
        @returns items 0 0
        @returns request 1 1
        """
        if 'offlined' in response.body:
            self.logger.critical("Crawler couldn't get page - content is scrambled. Crawling aborted")
            return

        page_num = response.meta.get('page_num', -1)
        self.save_response(response, 'page%d.html' % page_num)

        next_chunk = self.gen_next_chunk(response.body)

        if next_chunk == '00000000-1' or page_num > 5:
            self.logger.info('Crawler finished a book. Thank you')
            yield scrapy.Request(self.logout_url, callback=self.parse_logout)

        next_page_url = self.page_url % (self.book_id, next_chunk)
        yield scrapy.Request(next_page_url, callback=self.parse_page, meta={'page_num': page_num+1} if page_num != -1 else {})

    def parse_logout(self, response):
        """
        parse logout response

        @url file:///tmp/ss2book/invalid_username_password.html
        @returns items 0 0
        @returns request 0 0
        """
        self.save_response(response, 'logout.html')
        if 'loginform' in response.body:
            self.logger.info('Crawler successfully logged out')
        else:
            self.logger.critical('Crawler was unable to log out.')

    def gen_next_chunk(self, body):
        cm_pattern = 'var cm = new Array\((.*?)\)'
        cm_payload = [i if len(i) == 2 else '0'+i for i in re.findall(cm_pattern, body)[-1].split(',')]
        self.logger.debug('cm_payload: %s', cm_payload)

        ax_pattern = 'var a(1|2|3|4|5) = new Array\(\d+,(\d+),\d+\)'
        ax_list = re.findall(ax_pattern, body)[-5:]
        self.logger.debug('ax_list: %s', ax_list)

        result = ''.join([cm_payload[int(value)] for _x, value in ax_list])
        self.logger.debug('next_chunk: %s', result)

        return result

    def save_response(self, response, filename):
        file_path = os.path.join(self.directory_path, filename)
        self.logger.debug('Saving response from %s to %s' % (response.url, file_path))
        with open(file_path, 'wb') as f:
            f.write(response.body)
