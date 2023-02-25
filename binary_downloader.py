import requests
import socket
from my_config import g_config
from tenacity import retry, stop_after_delay, stop_after_attempt, wait_random



socket.setdefaulttimeout(g_config.get_config("socket_timeout", 10))


class MyDownLoader(object):
    local_cache: dict

    def __init__(self):
        self.local_cache = {}


    def download_resource(self, src):

        split_res = src.split(sep='?', maxsplit=1)
        identifier = split_res[0]

        if identifier not in self.local_cache:
            res = self.download_from_src(src)
            return res
        else:
            return self.local_cache[src]

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def download_from_src(self, src):
        resp = requests.get(src, stream=True)
        return resp.raw.read()


g_downloader = MyDownLoader()
