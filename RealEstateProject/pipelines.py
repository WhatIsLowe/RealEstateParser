# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
from scrapy.exporters import JsonItemExporter, CsvItemExporter
from datetime import datetime
import os

# class RealestateprojectPipeline:
#     def process_item(self, item, spider):
#         return item

class JsonPipeline(object):
    def __init__(self):
        self.file = open("cian.json", 'ab')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False, indent=4)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
    
class CsvPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.spider)

    def __init__(self, spider):
        # Устанавливаем текущую дату
        current_date = datetime.now().date()
        
        # Создаем папку outputs/{имя паука} если не существует
        output_dir = os.path.join('outputs', spider.name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Открыываем файл для записи outputs/{имя паука}/csv-file
        self.file = open(os.path.join(output_dir, f"cian от {current_date}.csv"), 'ab')
        self.exporter = CsvItemExporter(self.file)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item