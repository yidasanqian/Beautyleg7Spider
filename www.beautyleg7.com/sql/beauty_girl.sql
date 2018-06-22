use beauty_girl;
CREATE TABLE `beauty7_album` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category` varchar(45) DEFAULT NULL,
  `album_url` varchar(256) NOT NULL COMMENT '专辑链接',
  `album_url_object_id` varchar(32) NOT NULL COMMENT '专辑链接唯一id',
  `album_title` varchar(255) NOT NULL COMMENT '专辑链接标题',
  `cover_url` varchar(256) DEFAULT NULL COMMENT '专辑封面链接',
  `number` varchar(45) DEFAULT NULL COMMENT '专辑编号',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_object_id_UNIQUE` (`album_url_object_id`),
  KEY `idx_category` (`category`),
  KEY `idx_create_date` (`create_date`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4

CREATE TABLE `beauty7_album_image` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `album_id` int(11) unsigned NOT NULL COMMENT 'beauty7_album表的主键',
  `item_url` varchar(256) NOT NULL COMMENT '专辑的内容条目链接',
  `item_url_object_id` varchar(32) NOT NULL COMMENT '专辑的内容条目链接唯一id',
  `item_url_list_json` text COMMENT '专辑的内容条目链接列表的json形式',
  `stage_name` varchar(45) DEFAULT NULL COMMENT '艺名',
  `publish_date` datetime DEFAULT NULL,
  `item_title` varchar(255) DEFAULT NULL COMMENT '链接内容标题',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_item_url_object_id` (`item_url_object_id`),
  KEY `idx_stage_name` (`stage_name`),
  KEY `idx_publish_date` (`publish_date`)
) ENGINE=InnoDB AUTO_INCREMENT=520 DEFAULT CHARSET=utf8mb4


