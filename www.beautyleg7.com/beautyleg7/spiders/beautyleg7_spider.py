#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import hashlib
import re
from datetime import datetime

import gevent
import requests
import scrapy
from gevent.pool import Pool
from lxml import etree
from scrapy.http import HtmlResponse
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from ..items import Album, AlbumImageRelationItem, AlbumItem, AlbumImageItem
from ..utils.const import const
from ..utils.redis_util import get_redis_conn_from_pool


class Beautyleg7Spider(scrapy.Spider):
    name = 'Beautyleg7Spider'
    # category_list = ['siwameitui', 'xingganmeinv', 'weimeixiezhen', 'ribenmeinv']
    category_list = ['siwameitui']
    start_urls = [('http://www.beautyleg7.com/' + category) for category in category_list]

    const.REPEATED_THRESHOLD = 10

    def __init__(self, name=None, **kwargs):
        super().__init__(name=None, **kwargs)

        self.db_session = None

        self.gevent_pool = Pool(32)

        self.redis_cmd = get_redis_conn_from_pool()

        self.ALBUM_URL_REDIS_KEY_PREFIX = "album_url"
        self.REDIS_LIMITER = ":"
        self.album_last_item_redis_unique_key = ""
        self.album_item = None
        self.album_image_item_list = []
        self.album_image_relation_item = AlbumImageRelationItem()

    def start_requests(self):
        mysql_host = self.crawler.settings.get("MYSQL_HOST")
        mysql_port = self.crawler.settings.get("MYSQL_PORT")
        mysql_user = self.crawler.settings.get("MYSQL_USER")
        mysql_password = self.crawler.settings.get("MYSQL_PASSWORD")
        mysql_db_name = self.crawler.settings.get("MYSQL_DB_NAME")
        engine = create_engine('mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(mysql_user, mysql_password,
                                                                              mysql_host, mysql_port,
                                                                              mysql_db_name),
                               pool_recycle=180, echo=False)
        session_maker = sessionmaker(bind=engine)
        self.db_session = session_maker()

        for url in self.start_urls:
            yield scrapy.Request(url)

    def parse(self, response):
        if self.db_session is None:
            self.logger.error("db_session is None")
            return None
        repeated_count = 0
        if response is None:
            self.logger.warn("响应为空，不做处理！")
        else:
            album_nodes = response.css('.pic .item')
            category = response.css('.sitepath a')[1].css('a::text').extract_first().strip()

            # 判断最后一页的最后主题是否被持久化
            is_persisted_last_item = self.redis_cmd.get(self.album_last_item_redis_unique_key)
            is_last_item_finished = False
            if is_persisted_last_item is not None and int(is_persisted_last_item):
                is_last_item_finished = True
                self.logger.info("已持久化最后一页的最后主题：%s" % self.album_last_item_redis_unique_key)

            # 如果是最后一页则设置Redis存储key:“最后一页页码：最后一条主题url”，value：is_persisted（取值为0或1，默认为0）
            album_last_page_url = response.meta.get("album_last_page_url")
            if album_last_page_url is not None:
                album_last_page_url_last_item_redis_suffix = album_nodes[-1].css('.p a::attr(href)').extract_first()
                self.album_last_item_redis_unique_key = self.ALBUM_URL_REDIS_KEY_PREFIX + self.REDIS_LIMITER + \
                                                        self.sub_url_scheme(album_last_page_url,
                                                                            "") + self.REDIS_LIMITER + \
                                                        self.sub_url_scheme(album_last_page_url_last_item_redis_suffix,
                                                                            "")

                self.redis_cmd.setnx(self.album_last_item_redis_unique_key, 0)

            for album_node in album_nodes:
                album_url = album_node.css('.p a::attr(href)').extract_first().strip()
                # 判断当前主题url是否已持久化
                is_persisted = self.redis_cmd.get(album_url)
                if is_persisted is not None and int(is_persisted):
                    self.logger.info("Redis中该url album_url：%s已持久化" % album_url)
                    continue

                album_url_object_id = self.get_md5(album_url)
                # 只有name不存在时，当前set操作才执行
                self.redis_cmd.setnx(album_url, 0)
                count = 0
                try:
                    count = self.db_session.query(func.count()).filter(
                        Album.album_url_object_id == album_url_object_id).first()
                    if count:
                        count = count[0]
                except Exception as e:
                    self.logger.error("查询数据库异常，原因：{}".format(e))
                finally:
                    self.db_session.rollback()

                if count:
                    self.logger.info("数据库已有该数据album_url_object_id：%s" % album_url_object_id)
                    repeated_count += 1
                    # 只有name存在时，当前set操作才执行
                    self.redis_cmd.set(album_url, 1, xx=True)
                    continue
                else:
                    album_item = self.parse_album_item(album_node, album_url, album_url_object_id, category)
                    yield response.follow(url=album_url,
                                          meta={"AlbumItem": album_item},
                                          callback=self.parse_detail)

            # 提取下一页并交给scrapy下载
            selector_list = response.css('.page li a::attr(href)')
            # 如果最后一页的最后一个主题url未被持久化则继续爬取
            if not is_last_item_finished:
                if selector_list:
                    next_url = selector_list[-2].extract()
                    # todo 这里需要根据category来判断获取的最后一页url
                    album_last_page_url = None
                    last_page_url = selector_list[-1].extract()
                    if next_url == last_page_url:
                        album_last_page_url = response.urljoin(last_page_url)
                        self.logger.info("Last page：%s" % album_last_page_url)
                    else:
                        self.logger.info("Next page：%s" % response.urljoin(next_url))
                    yield response.follow(url=next_url,
                                          meta={"album_last_page_url": album_last_page_url},
                                          callback=self.parse)
                else:
                    self.logger.info("selector_list is None")
                    self.logger.info("重复次数：%s" % repeated_count)
            else:
                self.logger.info("Stop crawler. None Next page!")

    def parse_album_item(self, album_node, album_url, album_url_object_id, category):
        album_title = album_node.css('.p a img::attr(alt)').extract_first().strip()
        cover_url = album_node.css('.p a img::attr(src)').extract_first().strip()
        regex = "\d+\.\d+.\d+\s+No\.\d+|\d+\-\d+-\d+\s+No\.\d+"
        number_group = re.findall(regex, album_title)
        if number_group.__len__() > 0:
            number = number_group[0]
        else:
            number = "No.unknown"
        create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        album_item = AlbumItem()
        album_item['category'] = category
        album_item['album_url'] = album_url
        album_item['album_url_object_id'] = album_url_object_id
        album_item['album_title'] = album_title
        album_item['cover_url'] = cover_url
        album_item['number'] = number
        album_item['create_date'] = create_date
        return album_item

    def parse_detail(self, response):
        self.album_item = response.meta.get("AlbumItem")
        self.album_image_relation_item['album_item'] = self.album_item
        self.parse_album_image_item(response)
        # 详情页分页链接,循环生成所有子页面的请求
        relative_next_page_list = response.css('.page li a::attr(href)').extract()
        # 使用gevent协程池提升网络IO处理效率
        next_page_threads = [
            self.gevent_pool.spawn(self.get_album_image_item_list, response.urljoin(relative_next_page))
            for relative_next_page in relative_next_page_list[2:-1]
        ]
        gevent.joinall(next_page_threads)
        self.album_image_relation_item['album_image_item_list'] = self.album_image_item_list
        # 重新初始化
        self.album_image_item_list = []
        yield self.album_image_relation_item

    def get_album_image_item_list(self, abs_next_page):
        """
        使用下页绝对路径同步请求
        :param abs_next_page:
        :return:
        """
        resp = requests.get(abs_next_page)
        if resp.status_code == 200:
            encoding = requests.utils.get_encodings_from_content(resp.text)
            resp.encoding = encoding[0]
            self.parse_album_image_item(etree.HTML(resp.text))
        else:
            self.logger.warn("下载此页{}失败,返回的状态码为{}".format(abs_next_page, resp.status_code))

    def parse_album_image_item(self, response):
        """
        解析item并返回给pipelines
        :param response: 如果response类型是继承自scrapy的TextResponse类则使用scrapy的Selector来解析，否则使用lxml来解析
        :return:
        """
        if isinstance(response, HtmlResponse):
            item_title = response.xpath('//div[@class="content"]/h1/text()').extract_first().strip()
            publish_date = response.xpath('//div[@class="tit"]/span/text()').extract_first().split(":")[1]
            image_link_list = response.css('.contents a img::attr(src)').extract()
        else:
            item_title = response.xpath('//div[@class="content"]/h1/text()')[0].strip()
            publish_date = response.xpath('//div[@class="tit"]/span/text()')[0].split(":")[1]
            image_link_list = response.xpath('//div[@class="contents"]/a/img')
            image_link_list = [image_link.attrib['src'] for image_link in image_link_list]

        regex = "\s?\w+(\(|\[|\s?)[^\w]?"
        regex_group = re.findall(regex, item_title)
        stage_name = "unknown"

        if len(regex_group) > 0:
            str = regex_group[-1]
            if "[" in str:
                stage_name = str.split("[")[0].strip()
            elif "(" in str:
                stage_name = str.split("(")[0].strip()
            elif re.match("\w*", str):
                stage_name = str

        # 详情页多个图片链接
        for image_url in image_link_list:
            album_image_item = AlbumImageItem()
            album_image_item['item_url'] = image_url
            album_image_item['item_url_object_id'] = self.get_md5(image_url)
            item_url_list_json = "{}"
            album_image_item['item_url_list_json'] = item_url_list_json
            album_image_item['item_title'] = item_title
            album_image_item['stage_name'] = stage_name
            album_image_item['publish_date'] = publish_date
            self.album_image_item_list.append(album_image_item)
        return self.album_image_item_list

    @staticmethod
    def get_md5(param):
        if isinstance(param, str):
            param = param.encode()
        m = hashlib.md5()
        m.update(param)
        return m.hexdigest()

    @staticmethod
    def sub_url_scheme(website, replace_str):
        scheme_regex = "^(http://|https://)"
        return re.sub(scheme_regex, replace_str, website)
