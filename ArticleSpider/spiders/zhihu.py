# -*- coding: utf-8 -*-
import base64
import datetime
import hmac
import json
import re
import time
import scrapy
from PIL import Image
from scrapy import Request, FormRequest
from hashlib import sha1
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuQuestionItem, ZhihuAnswerItem
from scrapy.http.cookies import CookieJar
try:
    import urlparse as parse
except:
    from urllib import parse


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D.topics&offset={1}&limit={2}&sort_by=default'
    agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
    headers = {
        "User-Agent": agent,
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/signup",
    }
    grant_type = b"password"
    client_id = b"c3cef7c66a1843f8b3a9e6a1e3160e20"
    source = b"com.zhihu.web"
    timestamp = str(int(time.time() * 1000)).encode()
    hmac_key = b"d1b964811afb40118a12068ff74a12f4"

    def parse(self, response):
        """
        提取html页面中的所有url， 并跟踪这些url进行下一步提取
        如果提取的url中格式为/question/xxx， 就下载之后直接进入解析函数
        :param response:
        :return:
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)

        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)  # 提取id或者带/answer
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                # question_id = match_obj.group(2)

                yield scrapy.Request(
                    url = request_url,
                    headers = self.headers,
                    callback = self.parse_question,
                )
                # break
                # 调试技巧, 加break语句，只发送一次请求, 将多余的请求注释掉，并加上pass语句
            else:
                # 如果不是question页面则直接进一步跟踪
                # pass
                yield scrapy.Request(
                    url = url,
                    headers = self.headers,
                    callback = self.parse,
                )

    def parse_question(self, response):
        # 处理question页面，从页面中提取具体的question item
        # 这个函数体中也可像parse函数那样跟踪url
        match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)  # 提取id或者带/answer
        if match_obj:
            question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css("title", "div[data-zop-question]::attr(data-zop-question)")  # 一个字典提取
            item_loader.add_css("topics", "div[data-zop-question]::attr(data-zop-question)")  # 一个字典提取
            """
            json.loads(d).get('title')  # title
            
            tp_l = json.loads(d)['topics'] 
            ",".join([d.get('name') for d in tp_l])  # topics
            """
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            # item_loader.add_css("answer_num", ".QuestionMainAction::text") # 正则提取
            item_loader.add_xpath("answer_num", "//*[@class='List-headerText']/span/text()|//*[@class='QuestionMainAction']/text()")
            """
            re.match(".*?([,\d]+).*", d).group(1).replace(",", "")  # int
            """
            item_loader.add_css("comments_num", ".QuestionHeader-Comment .Button::text")
            """
            re.match(".*?(\d+).*", d).group(1)  # int
            """
            item_loader.add_css("watch_user_num", ".QuestionFollowStatus-counts strong::text")
            """
            d.replace(",", "")
            """
            item_loader.add_css("click_num", ".QuestionFollowStatus-counts strong::text")  # 不能提取第一个
            question_item = item_loader.load_item()

            yield question_item
            yield scrapy.Request(
                url = self.start_answer_url.format(question_id, 0, 3),
                headers = self.headers,
                callback = self.parse_answer,
            )


    def parse_answer(self,response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else answer["excerpt"]
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(
                url = next_url,
                headers = self.headers,
                callback = self.parse_answer,
            )


    def get_signature(self):
        s = hmac.new(self.hmac_key, digestmod=sha1)
        s.update(self.grant_type)
        s.update(self.client_id)
        s.update(self.source)
        s.update(self.timestamp)
        return str(s.hexdigest())

    def start_requests(self):
        yield Request(
            url = "https://www.zhihu.com/api/v3/oauth/captcha?lang=en",
            headers = self.headers,
            callback = self.need_captcha,
        )

    def need_captcha(self, response):
        cap_json = json.loads(response.text)["show_captcha"]
        if cap_json:
            print("需要验证码")
            yield Request(
                url = "https://www.zhihu.com/api/v3/oauth/captcha?lang=en",
                headers = self.headers,
                method = "PUT",
                callback = self.get_captcha,
            )
        else:
            print("不需要验证码")
            post_data = {
                'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
                'grant_type': 'password',
                'timestamp': str(int(time.time() * 1000)),
                'source': 'com.zhihu.web',
                'signature': self.get_signature(),
                'username': '18801305865',
                'password': 'doc19921222',
                'captcha': "",
            }
            yield FormRequest(
                url = "https://www.zhihu.com/api/v3/oauth/sign_in",
                formdata = post_data,
                headers = self.headers,
                callback = self.check_login,
            )

    def get_captcha(self, response):
        try:
            img = json.loads(response.text)["img_base64"]
        except ValueError as e:
            print("获取img_base64失败")
        else:
            with open("captcha.jpg", "wb") as f:
                f.write(base64.b64decode(img))
            image = Image.open("captcha.jpg")
            image.show()
            cap = input("请输入验证码：")
            image.close()
            post_data = {"input_text": cap}
            yield FormRequest(
                url = "https://www.zhihu.com/api/v3/oauth/captcha?lang=en",
                formdata = post_data,
                headers = self.headers,
                callback = self.captcha_login,
            )

    def captcha_login(self, response):
        try:
            cap_result = json.loads(response.text)["success"]
            print(cap_result)
        except ValueError as e:
            print("获取success值失败")
        else:
            if cap_result:
                print("验证成功")
            post_data = {
                "client_id": self.client_id,
                "username": "18801305865",  # 输入知乎用户名
                "password": "doc19921222",  # 输入知乎密码
                "grant_type": self.grant_type,
                "source": self.source,
                "timestamp": self.timestamp,
                "signature": self.get_signature(),  # 获取签名
                "captcha": "",
                # "lang": "en",
                # "ref_source": "homepage",
                # "utm_source": "",
                }
            yield FormRequest(
                url = "https://www.zhihu.com/api/v3/oauth/sign_in",
                headers = self.headers,
                formdata = post_data,
                callback = self.check_login,
            )

    def check_login(self, response):
        resp_json = json.loads(response.text)
        print(resp_json)
        print("登录成功")
        yield Request(
            url = "https://www.zhihu.com",
            dont_filter = True,
            headers = self.headers,
        )
