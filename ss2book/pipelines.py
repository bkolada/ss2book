# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import re

class Ss2BookPipeline(object):
    def process_item(self, item, spider):
        return item


class CorrectLinksPipeline(object):

    LINK_PATTERN = r'viewer.asp\?bkid=\d+&amp;destid=.*?#(\d+)'

    def process_item(self, item, _spider):
        print 'process_item, num:', item['page_num']
        item['content'] = re.sub(self.LINK_PATTERN, r'#\1', item['content'])
        return item

