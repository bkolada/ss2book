# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class TitlePage(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    isbn = scrapy.Field()

class PageItem(scrapy.Item):
    page_num = scrapy.Field()
    content = scrapy.Field()

