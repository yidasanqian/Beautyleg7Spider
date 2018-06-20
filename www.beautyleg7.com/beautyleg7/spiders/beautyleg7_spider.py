#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import hashlib
import re
from datetime import datetime

import scrapy
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from ..items import Album, AlbumImageRelationItem, AlbumItem, AlbumImageItem
from ..utils.const import const


class Beautyleg7Spider(scrapy.Spider):
    name = 'Beautyleg7Spider'
    category_list = ['siwameitui', 'xingganmeinv', 'weimeixiezhen', 'ribenmeinv']
    start_urls = [('http://www.beautyleg7.com/' + category) for category in category_list]

    const.REPEATED_THRESHOLD = 10

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
            album_nodes = response.css('.pic')
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

            # todo 提取下一页并交给scrapy下载
            current_page = int(response.css('.page .thisclass').extract_first())
            next_url = response.css('.page li a::attr(href)').extract_first()
            # 如果url重复次数超过阈值则停止爬取
            if next_url and repeated_count < const.REPEATED_THRESHOLD:
                self.logger.info("Next page：%s" % next_url)
                yield response.follow(next_url, self.parse)
            else:
                self.logger.info("None Next page!重复次数：%s" % repeated_count)
                self.db_session.close()

    def parse_detail(self, response):
        album_item = response.meta.get("AlbumItem")
        album_images_item = AlbumImageItem()
        album_image_relation_item = AlbumImageRelationItem()
        album_image_relation_item['album_item'] = album_item

        item_title = response.xpath('//div[@class="content"]/h1/text()').extract_first().strip()
        regx = "\s?\w+\[[^\w]?"
        list = re.findall(regx, item_title)
        if list.__len__() > 0:
            stage_name = list[0].split("[")[0]
        else:
            stage_name = "unknown"
        publish_date = response.xpath('//div[@class="tit"]/span/text()').extract_first().split(":")[1]
        # todo 详情页多个图片链接
        image_link_list = response.css('.contents a img::attr(src)').extract()

        # album_image_relation_item['album_id'] = album_id
        # album_image_relation_item['item_url'] = item_url
        # album_image_relation_item['item_url_object_id'] = item_url_object_id
        album_image_relation_item['item_title'] = item_title
        album_image_relation_item['stage_name'] = stage_name
        album_image_relation_item['publish_date'] = publish_date
        # todo 详情页分页链接

    @staticmethod
    def get_md5(param):
        if isinstance(param, str):
            param = param.encode()
        m = hashlib.md5()
        m.update(param)
        return m.hexdigest()
