# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from .items import Album, AlbumImage


class Beautyleg7MySqlPipeline(object):

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        spider.db_session.close()

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
            spider.db_session.add_all(album_image_list)
            # 提交即保存到数据库:
            spider.db_session.commit()
            spider.redis_cmd.set(album_url, 1, xx=True)
            # 如果Redis存储的最后一页的最后一条主题url的key不为空，设置其值位1，代表已持久化
            if spider.album_last_item_redis_unique_key != "":
                spider.redis_cmd.set(spider.album_last_item_redis_unique_key, 1, xx=True)
        except Exception as e:
            spider.logger.error("插入数据库异常，原因：{}".format(e))
        finally:
            spider.db_session.rollback()
        return item
