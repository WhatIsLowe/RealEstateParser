# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RealestateprojectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class CianItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    address = scrapy.Field()
    url = scrapy.Field()
    ad_page = scrapy.Field()