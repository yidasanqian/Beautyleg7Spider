# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .items import Album, AlbumImage


class Beautyleg7MySqlPipeline(object):
    def __init__(self, mysql_host, mysql_port, mysql_user, mysql_password, mysql_db_name):
        # 初始化数据库连接:
        engine = create_engine('mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(mysql_user, mysql_password,
                                                                              mysql_host, mysql_port,
                                                                              mysql_db_name),
                               pool_recycle=180, echo=False)
        # 创建session_maker类型:
        session_maker = sessionmaker(bind=engine)
        self.db_session = session_maker()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_host=crawler.settings.get("MYSQL_HOST"),
            mysql_port=crawler.settings.get("MYSQL_PORT"),
            mysql_user=crawler.settings.get("MYSQL_USER"),
            mysql_password=crawler.settings.get("MYSQL_PASSWORD"),
            mysql_db_name=crawler.settings.get("MYSQL_DB_NAME"),
        )

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        self.db_session.close()

    def process_item(self, item, spider):
        # AlbumItem
        album_item = item['album_item']
        # AlbumImageItem list
        album_image_item_list = item['album_image_item_list']
        category = album_item['category']
        album_url = album_item['album_url']
        album_url_object_id = album_item['album_url_object_id']
        album_title = album_item['album_title']
        cover_url = album_item['cover_url']
        number = album_item['number']
        create_date = album_item['create_date']
        album = Album(category, album_url, album_url_object_id, album_title, cover_url, number, create_date)
        try:
            # album_id 关联id验证
            album_image_list = []
            for album_image_item in album_image_item_list:
                item_url = album_image_item['item_url']
                item_url_object_id = album_image_item['item_url_object_id']
                item_url_list_json = album_image_item['item_url_list_json']
                item_title = album_image_item['item_title']
                stage_name = album_image_item['stage_name']
                publish_date = album_image_item['publish_date']
                album_image = AlbumImage(item_url, item_url_object_id, item_url_list_json, item_title, stage_name,
                                         publish_date, album)
                album_image_list.append(album_image)
            self.db_session.add_all(album_image_list)
            # 提交即保存到数据库:
            self.db_session.commit()
        except Exception as e:
            spider.logger.error("插入数据库异常，原因：{}".format(e))
            self.db_session.rollback()
        return item
