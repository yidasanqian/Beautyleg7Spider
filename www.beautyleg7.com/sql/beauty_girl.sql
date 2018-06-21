use beauty_girl;
create table beauty7_album
(
	id int unsigned auto_increment
		primary key,
	category varchar(45) null,
	album_url varchar(256) not null comment '专辑链接',
	album_url_object_id varchar(32) not null comment '专辑链接唯一id',
	album_title varchar(255) not null comment '专辑链接标题',
	cover_url varchar(256) null comment '专辑封面链接',
	number varchar(45) null comment '专辑编号',
	create_date datetime null comment '创建时间',
	constraint url_object_id_UNIQUE
		unique (album_url_object_id)
) engine=InnoDB;

create table beauty7_album_image
(
	id int unsigned auto_increment
		primary key,
	album_id int(11) unsigned not null comment 'beauty7_album表的主键',
	item_url varchar(256) not null comment '专辑的内容条目链接',
	item_url_object_id varchar(32) not null comment '专辑的内容条目链接唯一id',
	item_url_list_json text null comment '专辑的内容条目链接列表的json形式',
	stage_name varchar(45) null comment '艺名',
	publish_date datetime null,
	item_title varchar(255) null comment '链接内容标题',
	constraint beauty7__UNIQUE
		unique (item_url_object_id)
) engine=InnoDB;


