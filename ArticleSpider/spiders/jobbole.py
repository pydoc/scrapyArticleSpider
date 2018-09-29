# -*- coding: utf-8 -*-
import re
from urllib import parse
import datetime

import scrapy
from scrapy.http import Request
from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5

from scrapy.loader import ItemLoader


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        2. 获取下一页的url并交给scrapy进行下载,下载完成后交给parse
        """
        #解析列表页中的所有文章url并交给scrapy下载后并进行解析
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            post_url = post_node.css("::attr(href)").extract_first("")
            image_url = post_node.css("img::attr(src)").extract_first("")
            # 将Request交给scrapy下载,加 yield 语句
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url}, callback=self.parse_detail)
            # meta 是将列表页中不一定唯一存在的url -> Request -> response

        # 提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse)


    def parse_detail(self, response):
        # Request的回调函数
        # 提取文章的具体字段

        # article_item = JobBoleArticleItem()

        # front_image_url = response.meta.get("front_image_url", "") # 获取文章封面图,用get方法不会抛异常
        # title = response.xpath("//*[@class='entry-header']/h1/text()").extract_first("")
        # create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract_first("").strip()[:10]
        # praise_nums = response.xpath("//span[contains(@class, 'vote-post-up')]/h10/text()").extract_first("")
        # fav_nums = response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract_first("")
        # match_fav = re.match(".*?(\d+).*", fav_nums)
        # if match_fav:
        #     fav_nums = int(match_fav.group(1))
        # else:
        #     fav_nums = 0
        #
        # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first("")
        # match_com = re.match(".*?(\d+).*", comment_nums)
        # if match_com:
        #     comment_nums = int(match_com.group(1))
        # else:
        #     comment_nums = 0
        #
        # content = response.xpath("//div[@class='entry']").extract_first("")
        # tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ",".join(tag_list)
        #
        # article_item["url_object_id"] = get_md5(response.url) # 将url进行md5编码保存
        # article_item["title"] = title
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()  # 转换成日期
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()  # 获取当前如期
        # article_item["create_date"] = create_date
        # article_item["url"] = response.url
        # article_item["front_image_url"] = [front_image_url]  # 下载图片需要数组
        # article_item["praise_nums"] = praise_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["content"] = content
        # article_item["tags"] = tags


        # 通过item loader加载item
        front_image_url = response.meta.get("front_image_url", "") # 获取文章封面图,用get方法不会抛异常
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_xpath("title", "//*[@class='entry-header']/h1/text()")
        item_loader.add_xpath("create_date", "//p[@class='entry-meta-hide-on-mobile']/text()")
        item_loader.add_value("url", response.url)
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_value("url_object_id", response.url)
        item_loader.add_xpath("praise_nums", "//span[contains(@class, 'vote-post-up')]/h10/text()")
        item_loader.add_xpath("comment_nums", "//a[@href='#article-comment']/span/text()")
        item_loader.add_xpath("fav_nums", "//span[contains(@class, 'bookmark-btn')]/text()")
        item_loader.add_xpath("content", "//div[@class='entry']")
        item_loader.add_xpath("tags", "//p[@class='entry-meta-hide-on-mobile']/a/text()")

        article_item = item_loader.load_item()


        # 传递到pipelines.py
        yield article_item
