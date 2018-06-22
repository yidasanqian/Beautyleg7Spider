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


class Beautyleg7Spider(scrapy.Spider):
    name = 'Beautyleg7Spider'
    category_list = ['siwameitui', 'xingganmeinv', 'weimeixiezhen', 'ribenmeinv']
    start_urls = [('http://www.beautyleg7.com/' + category) for category in category_list]

    const.REPEATED_THRESHOLD = 10

    def __init__(self, name=None, **kwargs):
        super().__init__(name=None, **kwargs)
        self.db_session = None
        self.gevent_pool = Pool(16)

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
            category = response.css('.sitepath a')[1].css('a::text').extract_first().strip()
            album_nodes = response.css('.pic .item')
            for album_node in album_nodes:
                album_url = album_node.css('.p a::attr(href)').extract_first().strip()
                album_url_object_id = self.get_md5(album_url)
                count = 0
                try:
                    count = self.db_session.query(func.count()).filter(
                        Album.album_url_object_id == album_url_object_id).first()
                    if count:
                        count = count[0]
                except Exception as e:
                    self.logger.error("查询数据库异常，原因：{}".format(e))

                if count:
                    self.logger.info("数据库已有该数据album_url_object_id：%s" % album_url_object_id)
                    repeated_count += 1
                    continue
                else:
                    album_title = album_node.css('.p a img::attr(alt)').extract_first().strip()
                    cover_url = album_node.css('.p a img::attr(src)').extract_first().strip()
                    regx = "\d+\.\d+.\d+\s+No\.\d+"
                    list = re.findall(regx, album_title)
                    if list.__len__() > 0:
                        number = list[0]
                    else:
                        number = "No.0"
                    create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    album_item = AlbumItem()
                    album_item['category'] = category
                    album_item['album_url'] = album_url
                    album_item['album_url_object_id'] = album_url_object_id
                    album_item['album_title'] = album_title
                    album_item['cover_url'] = cover_url
                    album_item['number'] = number
                    album_item['create_date'] = create_date
                    yield response.follow(url=album_url,
                                          meta={"AlbumItem": album_item},
                                          callback=self.parse_detail)

            # 提取下一页并交给scrapy下载
            next_url = response.css('.page li a::attr(href)').extract_first()
            # 如果url重复次数超过阈值则停止爬取
            if next_url and repeated_count < const.REPEATED_THRESHOLD:
                self.logger.info("Next page：%s" % next_url)
                yield response.follow(next_url, self.parse)
            else:
                self.logger.info("None Next page!重复次数：%s" % repeated_count)
                self.db_session.close()

    def parse_detail(self, response):
        self.album_item = response.meta.get("AlbumItem")
        self.album_image_relation_item['album_item'] = self.album_item
        self.parse_image_item(response)
        # 详情页分页链接,循环生成所有子页面的请求
        relative_next_page_list = response.css('.page li a::attr(href)').extract()
        # 使用gevent协程池提升网络IO处理效率
        next_page_threads = [
            self.gevent_pool.spawn(self.get_album_image_list, response.urljoin(relative_next_page))
            for relative_next_page in relative_next_page_list[2:-1]
        ]
        gevent.joinall(next_page_threads)
        self.album_image_relation_item['album_image_item_list'] = self.album_image_item_list
        # 重新初始化
        self.album_image_item_list = []
        yield self.album_image_relation_item

    # 执行并获取响应列表（处理异常）
    # def exception_handler(self, request, exception):
    #     self.logger.error("请求url：%s,异常:%s" % (request.url, exception))

    def get_album_image_list(self, abs_next_page):
        """
        使用下页绝对路径同步请求
        :param abs_next_page:
        :return:
        """
        resp = requests.get(abs_next_page)
        if resp.status_code == 200:
            encoding = requests.utils.get_encodings_from_content(resp.text)
            resp.encoding = encoding[0]
            self.parse_image_item(etree.HTML(resp.text))
        else:
            self.logger.warn("下载此页{}失败,返回的状态码为{}".format(abs_next_page, resp.status_code))

    def parse_image_item(self, response):
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

        regex = "\s?\w+\[[^\w]?"
        regex_group = re.findall(regex, item_title)
        if regex_group.__len__() > 0:
            stage_name = regex_group[0].split("[")[0].strip()
        else:
            stage_name = "unknown"

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
