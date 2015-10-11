# -*- coding: utf-8 -*-
import scrapy
import os, sys
from ss2book import settings
from ss2book.items import PageItem
import re


class SkillportSpider(scrapy.Spider):
    name = 'skillport'
    allowed_domains = ['mobile.skillport.books24x7.com', 'secure.books24x7.com']
    login_url = 'https://secure.books24x7.com/express/login.asp'
    mobile_login_url = 'http://mobile.skillport.books24x7.com/login.asp'
    page_url = 'http://mobile.skillport.books24x7.com/viewer.asp?bookid=%s&chunkid=%s'
    logout_url = 'http://mobile.skillport.books24x7.com/abandonsession.asp'

    def __init__(self, book_id='62126', max_page_num=sys.maxsize, *args, **kwargs):
        super(SkillportSpider, self).__init__(*args, **kwargs)
        self.book_id = book_id
        self.max_page_num = int(max_page_num)
        self.directory_path = os.path.join(settings.TMP_DIR, self.book_id, "source")
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

        self.directory_path_raw = os.path.join(settings.TMP_DIR, self.book_id, "raw")
        if not os.path.exists(self.directory_path_raw):
            os.makedirs(self.directory_path_raw)

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
        @returns items 1 1
        @returns request 1 1
        """
        if '>offlined</A>' in response.body:
            self.save_response(response, 'page-scrambled.html')
            self.logger.critical("Crawler couldn't get page - content is scrambled. Crawling aborted")
            yield scrapy.Request(self.logout_url, callback=self.parse_logout)

        page_num = response.meta.get('page_num', -1)
        self.save_response(response, 'page%d.html' % page_num)

        yield PageItem(page_num = page_num, content = response.xpath('//div[@style="clear:both"][1]/following-sibling::div[1]').extract()[0].encode('utf8'))
        self.save_raw_content(
            response.xpath('//div[@style="clear:both"][1]/following-sibling::div[1]').extract()[0].encode('utf8'),
            'page%d.html' % page_num)

        next_chunk = self.gen_next_chunk(response.body)
        if next_chunk == '00000000-1' or page_num > self.max_page_num:
            self.logger.info('Crawler finished a book. Thank you')
            yield scrapy.Request(self.logout_url, callback=self.parse_logout)
        else:
            next_page_url = self.page_url % (self.book_id, next_chunk)
            meta = {'page_num': page_num + 1} if page_num != -1 else {}
            yield scrapy.Request(next_page_url, callback=self.parse_page, meta=meta)

    def parse_logout(self, response):
        """
        parse logout response
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
        "it could become deprecated"
        file_path = os.path.join(self.directory_path, filename)
        self.logger.debug('Saving response from %s to %s' % (response.url, file_path))
        with open(file_path, 'wb') as f:
            f.write(response.body)

    def save_raw_content(self, content, filename):
        file_path = os.path.join(self.directory_path_raw, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
