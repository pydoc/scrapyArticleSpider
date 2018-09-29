# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import datetime
import json
import re

import scrapy
from scrapy.loader import ItemLoader
# from scrapy.loader import Identity #  解决front_image_url下载会抛异常的解决办法之一
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from ArticleSpider.utils.common import get_md5, extract_num
from ArticleSpider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from w3lib.html import remove_tags



class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

def add_jobbole(value):
    # value是title里得到的实际值
    return value + "-doc"

# 两个函数之间空两行,为符合pep8规范
def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()  # 转换成日期
    except Exception as e:
        create_date = datetime.datetime.now().date()
    return create_date

# 将这个处理数字方法放到utils的common中
# def get_nums(value):
#     match_com = re.match(".*?(\d+).*", value)
#     if match_com:
#         nums = int(match_com.group(1))
#     else:
#         nums = 0
#     return nums


def remove_comment_tags(value):
    if "评论" in value:
        return ""
    else:
        return value


def return_value(value):
    return value


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


class LagouItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field(
        # input_processor 可以将title中的值经过MapCompose中的函数进行预处理
        # MapCompose 中传递任意多函数
        # MapCompose 也可以传递一个lambda函数, 如: lambda x: x + "-jobbole"
        # input_processor = MapCompose(lambda x: x + "-jobbole", add_jobbole)
    )
    create_date = scrapy.Field(
        input_processor = MapCompose(date_convert)
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field(
        input_processor = MapCompose(get_md5)
    )
    front_image_url = scrapy.Field(
        # 用了自定义itemloader的deafult_output_processor之后就变成了字符串,
        # 当交给imagepipeline下载的时候, 就会抛异常
        output_processor = MapCompose(return_value)
        # 用一个返回原值的函数起到了如下有点:
        # 1. 没有修改front_image_url中的值
        # 2. 覆盖掉default_output_processor
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field()
    comment_nums = scrapy.Field(
        input_processor = MapCompose(extract_num)
    )
    fav_nums = scrapy.Field(
        input_processor = MapCompose(extract_num)
    )
    tags = scrapy.Field(
        input_processor = MapCompose(remove_comment_tags),
        # tags 本身就是list, 所以用Join
        output_processor = Join(",")
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        # 类似django的model，将sql语句写入item的实例中
        insert_sql = """
            insert into jobbole_article(title, url, create_date, fav_nums, url_object_id, front_image_url,
              comment_nums, praise_nums, tag, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE fav_nums=VALUES(fav_nums),
              comment_nums=VALUES(comment_nums), praise_nums=VALUES(praise_nums), content=VALUES(content)
        """
        params = (self["title"], self["url"], self["create_date"], self["fav_nums"], self["url_object_id"],
            self["front_image_url"][0], self["comment_nums"], self["praise_nums"], self["tags"], self["content"])
        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    # 知乎 question item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    # creat_time = scrapy.Field()
    # update_time = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()
    # craw_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num,
              click_num, crawl_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num), crawl_time=VALUES(crawl_time)
        """

        zhihu_id = self["zhihu_id"][0]
        topics = ",".join([d.get("name") for d in json.loads(self["topics"][0])["topics"]])
        url = self["url"][0]
        title = "".join(json.loads(self["title"][0]).get("title"))
        content = "".join(self["content"][0])
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))
        watch_user_num = extract_num("".join(self["watch_user_num"][0]))
        click_num = extract_num("".join(self["click_num"][1]))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, click_num, crawl_time)
        return insert_sql, params

class ZhihuAnswerItem(scrapy.Item):
    # 知乎 answer item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()
    # crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, praise_num, comments_num, 
                create_time, update_time, crawl_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(content), praise_num=VALUES(praise_num),
                comments_num=VALUES(comments_num), update_time=VALUES(update_time), crawl_time=VALUES(crawl_time)
        """

        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"], self["author_id"], self["content"],self["praise_num"],
            self["comments_num"], create_time, update_time, self["crawl_time"].strftime(SQL_DATETIME_FORMAT)
        )

        return insert_sql, params


def remove_splash(value):
    # 去掉工作城市的斜线
    return value.replace("/", "").strip()

def remove_strip(value):
    # 去掉\n \s
    return re.sub("[\n\s]+", "", value)[:-4]

# def handle_publish_time(value):
#     # 取推送时间
#     return value.split()[0]


class LagouJobItem(scrapy.Item):
    # 拉钩网职位信息
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field(
        input_processor = MapCompose(remove_splash)
    )
    job_city = scrapy.Field(
        input_processor = MapCompose(remove_splash)
    )
    work_years = scrapy.Field(
        input_processor = MapCompose(remove_splash)
    )
    degree_need = scrapy.Field(
        input_processor = MapCompose(remove_splash)
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field(
        # input_processor = MapCompose(handle_publish_time)
    )
    tags = scrapy.Field(
        input_processor = Join(",")
    )
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor = MapCompose(remove_tags, str.strip)
    )
    job_addr = scrapy.Field(
        input_processor = MapCompose(remove_tags, str.strip, remove_strip)
    )
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(url, url_object_id, title, salary, job_city, work_years, degree_need, job_type, publish_time, tags, job_advantage,
            job_desc, job_addr, company_url, company_name, crawl_time)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE salary=VALUES(salary),
            publish_time=VALUES(publish_time), job_advantage=VALUES(job_advantage), job_desc=VALUES(job_desc), crawl_time=VALUES(crawl_time)
        """
        params = (self["url"], self["url_object_id"], self["title"], self["salary"], self["job_city"], self["work_years"],
            self["degree_need"], self["job_type"], self["publish_time"], self["tags"], self["job_advantage"],
            self["job_desc"], self["job_addr"], self["company_url"], self["company_name"], self["crawl_time"].strftime(SQL_DATETIME_FORMAT)
        )

        return insert_sql, params
