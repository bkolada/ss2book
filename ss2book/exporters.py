# -*- coding: utf-8 -*-
import scrapy
from scrapy.exporters import BaseItemExporter
from ss2book import settings

class FuseExporter(BaseItemExporter):

    def __init__(self, file, **kwargs):
        self._configure(kwargs)
        self.file = file

    def export_item(self, item):
        self.file.write(item['content'])
