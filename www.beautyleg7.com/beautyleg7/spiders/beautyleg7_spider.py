#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..utils.const import const


class Beautyleg7Spider(scrapy.Spider):
    name = 'Beautyleg7Spider'
    allow_domain = ['http://www.beautyleg7.com']
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
        pass
