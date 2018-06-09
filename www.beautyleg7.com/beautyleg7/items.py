# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base


class AlbumItem(scrapy.Item):
    category = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    title = scrapy.Field()
    cover_url = scrapy.Field()
    number = scrapy.Field()
    create_date = scrapy.Field()


class AlbumImagesItem(scrapy.Item):
    album_id = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    title = scrapy.Field()
    stage_name = scrapy.Field()
    publish_date = scrapy.Field()


Base = declarative_base()


class Album(Base):
    __tablename__ = 'beauty7_album'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(45))
    url = Column(String(256))
    url_object_id = Column(String(45), unique=True)
    title = Column(String(45))
    cover_url = Column(String(256))
    number = Column(String(45))
    create_date = Column(DateTime)

    def __init__(self, category, url, url_object_id, title, cover_url, number, create_date):
        self.category = category
        self.url = url
        self.url_object_id = url_object_id
        self.title = title
        self.cover_url = cover_url
        self.number = number
        self.create_date = create_date


class AlbumImages(Base):
    __tablename__ = 'beauty7_album_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    album_id = Column(Integer)
    url = Column(String(256))
    url_object_id = Column(String(45), unique=True)
    title = Column(String(45))
    stage_name = Column(String(45))
    publish_date = Column(DateTime)

    def __init__(self, album_id, url, url_object_id, title, stage_name, publish_date):
        self.album_id = album_id
        self.url = url
        self.url_object_id = url_object_id
        self.title = title
        self.stage_name = stage_name
        self.publish_date = publish_date
