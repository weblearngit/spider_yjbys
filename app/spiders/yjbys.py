# -*- coding: utf-8 -*-
"""
@desc: 应届毕业生网
@version: python3
@author: shhx
@time: 2022-05-24 15:40:02
"""
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from apputils.yw_common import get_now_filename


def get_settings():
    settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # "app.middlewares.proxy_request.ProxyMiddleware": 125,
        },
        "ITEM_PIPELINES": {"rapp.pipelines.file_save.TxtPipeline": 1},
        "TXT_SAVE": {
            "output_path": f"E:/Z_ES_DATA/output-{get_now_filename()}.txt",
            "flush_data_length": 100,
        },
        "DOWNLOAD_TIMEOUT": 20,
    }
    return settings


class YjbysSpider(CrawlSpider):
    name = "yjbys"
    allowed_domains = ["yjbys.com"]
    # 多级目录，需要抓取多遍
    start_urls = ["http://yjbys.com/"]

    custom_settings = get_settings()

    rules = (
        # 先抓取全部url，之后针对性过滤
        Rule(LinkExtractor(allow=r"/.*"), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        row_dict = {"page_url": response.url}
        yield row_dict
