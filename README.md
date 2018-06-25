# Beautyleg7Spider

#### 项目介绍
一个利用Scrapy框架实现的完整的爬取www.beautyleg7.com网站所有图片的爬虫

#### 软件架构
软件架构说明


#### 安装教程

[sql脚本](www.beautyleg7.com/sql/beauty_girl.sql)

```
pip install pywin32
pip install mysql-connector-python
pip install Pillow
pip install PyMySQL
pip install redis
pip install Scrapy
pip install scrapyd
pip install scrapyd-client
pip install SQLAlchemy
pip install pymongo
pip install gevent
```

#### 使用说明


#### 技术要点
[爬虫高性能相关（协程效率最高，IO密集型）](https://www.cnblogs.com/jokerbj/p/8283853.html)

[Grequests VS aiohttp+asyncio](https://blog.csdn.net/getcomputerstyle/article/details/78446892)

**爬取过程出现异常中断的解决方案：**

1. 爬取前记录当前爬取的主题页面的URL，存储到Redis key：URL，value：is_persisted（取值为0或1，默认为0）。
2. 当记录已存储到数据库后，设置Redis对应key的value为1（1表示已持久化到数据库）。
3. 若步骤1和2中间出现异常导致程序异常中断停止，则恢复时从Redis取得上次爬出的主题页面URL重新爬取。

**重复爬取主题页面URL的解决方案：**

1. Redis存储爬取最后一页的页码和最后一条主题URL key:最后一页页码：最后一条主题url，value：is_persisted（取值为0或1，默认为0）。 
2. 每次爬取时检查最后一页是否和Redis中存储的key相同，若不相同则更新key并设置值为0，否则继续下一步。
3. 当Redis中存储的key的value为1时，开始判断重复的主题URL数，当超过预设的阈值时停止爬取。

#### 参与贡献

1. Fork 本项目
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request