# -*- coding: utf-8 -*-
"""
@desc: 请示时使用代理
@version: python3
@author: shhx
@time: 2022/5/27 15:19
"""
from loguru import logger
import os
import requests
from twisted.internet.error import (
    ConnectionRefusedError,
    TimeoutError,
    TCPTimedOutError,
)
from apputils.yw_common import ProxyIP


def get_proxy_by_url():
    """
    代理云
    :return:
    """
    url = os.getenv("PROXY_IP_GET_URL")
    if not url:
        raise RuntimeError("没有可用的代理IP获取url")
    resp_ips = requests.get(url).text
    logger.info(resp_ips)
    line = resp_ips.strip().split(",")
    new_str = line[:2] + line[-2:]
    return ",".join(new_str)


class ProxyMiddleware(object):
    def __init__(self, max_failed=3, replace_proxy_auto=True):
        self.proxy_enabled = True
        # 主动替换出现异常的代理IP
        self.replace_proxy_auto = replace_proxy_auto
        self.proxy_utils = ProxyIP(get_proxy_by_url, max_failed=max_failed)

    def process_request(self, request, spider):
        if not self.proxy_enabled:
            if self.replace_proxy_auto:
                self.proxy_utils.reset()
                logger.info("======= 代理IP状态异常，主动换一个 =======")
            else:
                raise RuntimeError("代理IP状态异常")

        # 为每个request对象分配一个ip代理
        request.meta["proxy"] = self.proxy_utils.get_proxy()

    def process_response(self, request, response, spider):
        # 请求成功
        cur_proxy = request.meta.get("proxy")
        # 判断是否被对方禁封
        HTTPERROR_ALLOWED_CODES = spider.crawler.settings.get(
            "HTTPERROR_ALLOWED_CODES"
        )
        if (
            HTTPERROR_ALLOWED_CODES
            and response.status in HTTPERROR_ALLOWED_CODES
        ):
            return response
        # 失败了，处理一下代理IP
        if response.status > 400:
            logger.info(
                f"=========== 请求状态异常 {response.status=}  {response.url}"
            )
            self.proxy_utils.count_failed()
            # del request.meta["proxy"]
            # # 将这个请求重新给调度器，重新下载
            # return request
        else:
            # 成功一次就重置失败次数
            self.proxy_utils.reset_max_failed()
        # 状态码正常的时候，正常返回
        return response

    def process_exception(self, request, exception, spider):
        # 请求失败
        cur_proxy = request.meta.get("proxy")  # 取出当前代理

        # 如果本次请求使用了代理，并且网络请求报错，认为这个ip出了问题
        if cur_proxy and isinstance(
            exception, (ConnectionRefusedError, TimeoutError, TCPTimedOutError)
        ):
            logger.info(
                f"======== 当前的proxy {cur_proxy} 和 exception[{type(exception)}] {exception}"
            )
            self.proxy_utils.count_failed()
            del request.meta["proxy"]
            # 重新下载这个请求
            return request


class ProxyMiddlewareDebug(ProxyMiddleware):
    def __init__(self):
        super(ProxyMiddlewareDebug).__init__(replace_proxy_auto=False)
