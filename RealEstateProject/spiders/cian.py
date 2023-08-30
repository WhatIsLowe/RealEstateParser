import logging
import time
import undetected_chromedriver as uc
from ..items import CianItem

import scrapy
from scrapy import Spider
from scrapy import Selector
from scrapy.http import HtmlResponse
from scrapy.exceptions import CloseSpider

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.WARNING)

class CianSpider(Spider):
    name = 'cian'
    # custom_settings = {
    #     'FEED_FORMAT': 'json',
    #     'FEED_URI': 'cian.json'
    # }

    start_urls = [
        "https://kazan.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=1&region=4777&room1=1"
    ]

    current_url = "https://kazan.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=1&region=4777&room1=1"

    prev_page_number = 0

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        Создает экземпляр драйвера с помощью undetected_chromedriver
        и сохраняет его в атрибуте driver экземпляра паука
        """
        spider = super(CianSpider, cls).from_crawler(crawler, *args, **kwargs)
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--proxy-server=https://190.110.35.224:999")
        options.add_argument('--log-level=3')   # Устанавливаем уровень логирования на 3 (ОШИБКА (ERROR))
        spider.driver = uc.Chrome(options=options)
        # driver = uc.Chrome(browser_executable_path="../chromedriver", options=options)
        return spider

    def start_requests(self):
        """
        Генерирует начальные запросы паука

        Yields:
            scrapy.Request
        """
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'current_url': url})


    def parse(self, response):
        current_url = response.meta['current_url']
        self.driver.get(current_url)
        selector = Selector(text=self.driver.page_source)

        try:
            # Получаем номер текущей страницы
            page_number = int(current_url.split('&p=')[1].split('&')[0])
            self.logger.warn(f"Обрабатываю страницу №{page_number}")
        except IndexError:
            # Если номер страницы в адресе не найден => присваиваем 1
            page_number = 1

        # Если номер текущей страницы < номера предыдущей => завершаем работу паука
        if page_number < self.prev_page_number:
            raise CloseSpider("Достигнут предел страниц")
        else:
            self.prev_page_number = page_number

        # Проверяем наличие на странице контейнера с доп предложениями (появляется на последней странице)
        additional_block = response.xpath('//div[@data-name="Suggestions"]')
        if len(additional_block) != 0:
            response = self.click_more_button(current_url)

        # Получаем все объявления со страницы
        ads = response.xpath("//div[@class='_93444fe79c--content--lXy9G']").getall()

        # Извлекаем данные объвлений
        for ad in ads:
            data = Selector(text=ad)

            try:
                addr_div = data.xpath("//div[@class='_93444fe79c--labels--L8WyJ']")
                addr = self.extract_address(addr_div)
            except:
                addr = None

            item = CianItem()
            item['title'] = data.xpath('//span[@data-mark="OfferTitle"]//span//text()').get()
            item['price'] = data.xpath('//span[@data-mark="MainPrice"]//span//text()').get()[:-2].replace(" ", '')
            item['address'] = addr
            item['url'] = data.css('a._93444fe79c--link--eoxce::attr(href)').get()
            item['ad_page'] = page_number

            yield item

        # Переход на следующую страницу
        self.current_url = self.current_url.replace(f"p={page_number}", f"p={page_number + 1}")
        if self.current_url is not None:
            yield response.follow(self.current_url, self.parse, meta={'current_url': self.current_url})

    def extract_address(self, addr_div: Selector) -> str:
        """
        Объединяет адрес
        :param addr_div: элемент div содержащий адрес
        :return: строка с адресом
        """
        address_parts = addr_div.css('._93444fe79c--labels--L8WyJ a::text').getall()
        address = ', '.join(address_parts)
        return address

    def click_more_button(self, current_url) -> HtmlResponse:
        """
        Ищет и нажимает на кнопку "Показать еще" до тех пор, пока она есть
        :return:
        """
        # Открываем текущую страницу (страницу, на которой обнаружен контейнер с доп предложениями)
        self.driver.get(current_url)

        # Ждем загрузки страницы
        time.sleep(5)

        # На странице вероятно появление плашки о принятии файлов куки => принимаем
        try:
            accept_cookies_button = self.driver.find_element(By.XPATH, "//div[@data-name='CookiesNotification']"
                                                                       "//div[@class='_25d45facb5--button--CaFmg']")
            accept_cookies_button.click()
            time.sleep(2)
        except NoSuchElementException:
            pass

        while True:
            try:
                more_button = self.driver.find_element(By.CLASS_NAME,
                                                       '_93444fe79c--moreSuggestionsButtonContainer--h0z5t')
                more_button.click()
                time.sleep(5)
            except:
                break

        # Обновляем содержимое ответа Scrapy
        body = self.driver.page_source
        url = self.driver.current_url
        response = HtmlResponse(url=url, body=body, encoding='utf-8')
        return response

    def closed(self, reason):
        self.driver.quit()
        logging.info(msg="Работа завершена")
