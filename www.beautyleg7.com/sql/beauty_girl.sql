use beauty_girl;
CREATE TABLE `beauty7_album` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category` varchar(45) DEFAULT NULL,
  `album_url` varchar(256) NOT NULL COMMENT '专辑链接',
  `album_url_object_id` varchar(32) NOT NULL COMMENT '专辑链接唯一id',
  `album_title` varchar(45) NOT NULL COMMENT '专辑链接标题',
  `cover_url` varchar(256) DEFAULT NULL COMMENT '专辑封面链接',
  `number` varchar(45) DEFAULT NULL COMMENT '专辑编号',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_object_id_UNIQUE` (`album_url_object_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `beauty7_album_images` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `album_id` int(11) NOT NULL COMMENT 'beauty7_album表的主键',
  `item_url` varchar(256) NOT NULL COMMENT '专辑的内容条目链接',
  `item_url_object_id` varchar(32) NOT NULL COMMENT '专辑的内容条目链接唯一id',
  `item_title` varchar(45) DEFAULT NULL COMMENT '链接内容标题',
  `stage_name` varchar(45) DEFAULT NULL COMMENT '艺名',
  `publish_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `beauty7__UNIQUE` (`item_url_object_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
