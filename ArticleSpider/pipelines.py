# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi
import codecs
import json
import MySQLdb
import MySQLdb.cursors

# 跟数据库或文件打交道, 如将数据保存到mysql, mongodb, 发送到elasticsearch中进行检索
class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


# 调用scrapy提供的json exporter导出json文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open("articleexport.json", "wb")
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# 自定义保存至json文件
class JsonWithEncodingPipeline(object):
    def __init__(self):
        # 初始化用写的方式打开json文件
        self.file = codecs.open("article.json", "w", encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item  # 记得将item 返回回去,因为其他pipeline还要用
    def spider_closed(self, spider):  # 爬取完成就会执行
        self.file.close()


# 保存到mysql
class MysqlPipeline(object):
    # 采用同步的机制写入mysql
    # 入库的速度可能跟不上爬取的速度,就会造成阻塞,execute/commit 都是阻塞操作
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', '****', 'article_spider', charset='utf8', use_unicode=True)
        # 具体数据库操作使用cursor完成的
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        # %s 是占位符
        insert_sql = """
            insert into jobbole_article(title, url, create_date, fav_nums, url_object_id, front_image_url, comment_nums, praise_nums, tag, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (
            item["title"], item["url"], item["create_date"], item["fav_nums"], item["url_object_id"],
            item["front_image_url"], item["comment_nums"], item["praise_nums"], item["tags"], item["content"]
        ))
        self.conn.commit()

# mysql入库异步导入, 运用的是twisted
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        # 接受cls(dbpool)实例化的对象
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings): #  cls 是本身,即MysqlTwistedPipeline
        # 会被scrapy调用,直接使用settings.py的配置信息
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            password = settings["MYSQL_PASSWORD"],
            charset = "utf8",
            use_unicode = True,
            cursorclass = MySQLdb.cursors.DictCursor,
        )

        # 构建连接池, 传入dbapiname, 将上面的参数传递进去,利用dict的形式传递
        # MySQLdb的dict参数名必须与connection的参数名保持一致
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        # 执行异步操作之后可能会出错误的,不能等待异步操作的错误的返回
        query.addErrback(self.handle_error)   # 专门处理错误的函数


    def handle_error(self, failure):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        insert_sql = """
                    insert into jobbole_article(title, url, create_date, fav_nums, url_object_id, front_image_url, comment_nums, praise_nums, tag, content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
        cursor.execute(insert_sql, (
            item["title"], item["url"], item["create_date"], item["fav_nums"], item["url_object_id"],
            item["front_image_url"][0], item["comment_nums"], item["praise_nums"], item["tags"], item["content"]
        ))


# 绑定 front_image_path, 将文件路径放到这里
# 这个顺序靠后,所以已经经过ArticlespiderPipeline 处理了
class ArticleImagesPipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            # 有些网站是没有封面的,如知乎,所以要加一个判断
            # item是一个dict, 所以这种判断是有效的
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path
        return item
