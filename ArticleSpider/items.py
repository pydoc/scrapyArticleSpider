# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import datetime
import re

import scrapy
from scrapy.loader import ItemLoader
# from scrapy.loader import Identity #  解决front_image_url下载会抛异常的解决办法之一
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from ArticleSpider.utils.common import get_md5



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


def get_nums(value):
    match_com = re.match(".*?(\d+).*", value)
    if match_com:
        nums = int(match_com.group(1))
    else:
        nums = 0
    return nums


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
        input_processor = MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor = MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor = MapCompose(remove_comment_tags),
        # tags 本身就是list, 所以用Join
        output_processor = Join(",")
    )
    content = scrapy.Field()
