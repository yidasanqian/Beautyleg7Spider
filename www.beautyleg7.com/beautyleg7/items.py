# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


class AlbumItem(scrapy.Item):
    category = scrapy.Field()
    album_url = scrapy.Field()
    album_url_object_id = scrapy.Field()
    album_title = scrapy.Field()
    cover_url = scrapy.Field()
    number = scrapy.Field()
    create_date = scrapy.Field()


class AlbumImageItem(scrapy.Item):
    album_id = scrapy.Field()
    item_url = scrapy.Field()
    item_url_object_id = scrapy.Field()
    item_url_list_json = scrapy.Field()
    item_title = scrapy.Field()
    stage_name = scrapy.Field()
    publish_date = scrapy.Field()


class AlbumImageRelationItem(scrapy.Item):
    """
    用来临时存储AlbumItem和AlbumImageItem，作为spider向pipelines的传输对象
    """
    album_item = scrapy.Field()
    album_image_item_list = scrapy.Field()


Base = declarative_base()


class Album(Base):
    __tablename__ = 'beauty7_album'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(45))
    album_url = Column(String(256))
    album_url_object_id = Column(String(32), unique=True)
    album_title = Column(String(255))
    cover_url = Column(String(256))
    number = Column(String(45))
    create_date = Column(DateTime)

    def __init__(self, category, album_url, album_url_object_id, album_title, cover_url, number, create_date):
        self.category = category
        self.album_url = album_url
        self.album_url_object_id = album_url_object_id
        self.album_title = album_title
        self.cover_url = cover_url
        self.number = number
        self.create_date = create_date


class AlbumImage(Base):
    __tablename__ = 'beauty7_album_image'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 请注意，设置外键的时候用的是表名.字段名。其实在表和表类的抉择中，只要参数是字符串，往往是表名；如果是对象则是表类对象。
    album_id = Column(Integer, ForeignKey('beauty7_album.id'))
    item_url = Column(String(256))
    item_url_object_id = Column(String(32), unique=True)
    item_url_list_json = Column(Text)
    item_title = Column(String(255))
    stage_name = Column(String(45))
    publish_date = Column(DateTime)

    album = relationship('Album', backref='beauty7_album_image')

    def __init__(self, item_url, item_url_object_id, item_url_list_json, item_title, stage_name, publish_date, album):
        self.item_url = item_url
        self.item_url_object_id = item_url_object_id
        self.item_url_list_json = item_url_list_json
        self.item_title = item_title
        self.stage_name = stage_name
        self.publish_date = publish_date
        self.album = album
