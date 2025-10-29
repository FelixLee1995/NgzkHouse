import requests
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode
from tenacity import retry, stop_after_delay, stop_after_attempt, wait_random
from my_config import g_config
import socket
# 为所有请求设置默认超时
socket.setdefaulttimeout(g_config.get_config("socket_timeout", 10))


g_ngzk_headers  = {
                'Accept-Encoding': 'gzip',
                'Accept-Language': 'zh-Hans-CN;q=1.0,ja-CN;q=0.9,zh-Hant-CN;q=0.8',
                'Content-Length': '56',
                'Host': 'api.n46.glastonr.net',
                'User-Agent': 'Dart/3.7 (dart:io)',
                'X-Talk-App-ID': 'jp.co.sonymusic.communication.nogizaka 2.4',
                'x-talk-app-platform': 'ios',
                'Content-Type': 'application/json'
            }

g_skzk_headers  = {
                'Accept-Encoding': 'gzip',
                'Accept-Language': 'zh-Hans-CN;q=1.0,ja-CN;q=0.9,zh-Hant-CN;q=0.8',
                'Content-Length': '56',
                'Host': 'api.s46.glastonr.net',
                'User-Agent': 'Dart/3.7 (dart:io)',
                'X-Talk-App-ID': 'jp.co.sonymusic.communication.sakurazaka 2.4',
                'x-talk-app-platform': 'ios',
                'Content-Type': 'application/json'
            }

g_htzk_headers  = {
                'Accept-Encoding': 'gzip',
                'Accept-Language': 'zh-Hans-CN;q=1.0,ja-CN;q=0.9,zh-Hant-CN;q=0.8',
                'Content-Length': '56',
                'Host': 'api.kh.glastonr.net',
                'User-Agent': 'Dart/3.7 (dart:io)',
                'X-Talk-App-ID': 'jp.co.sonymusic.communication.keyakizaka 2.4',
                'x-talk-app-platform': 'ios',
                'Content-Type': 'application/json'
            }

@dataclass
class NgzkMsgGroup:
    Name: str
    Id: int
    Avatar: str
    AvailableTokenDict: dict

    def __init__(self, name, id, avatar) -> None:
        self.Name = name
        self.Id = id
        self.Avatar = avatar
        self.AvailableTokenDict = {}


class NgzkMsgApi(object):
    refresh_token: dict
    token: dict
    qry_timeout: int
    qry_history_spread: int
    qry_history_cnt: int
    qry_order: str
    g_sublist: dict

    def __init__(self):
        self.refresh_token = g_config.get_config("refresh_token", [])
        self.refresh_token_mapping = g_config.get_config("refresh_tokens", [])
        self.qry_timeout = g_config.get_config("qry_timeout", 3)
        self.qry_history_spread = g_config.get_config("qry_history_spread", 24)
        self.qry_history_cnt = g_config.get_config("qry_history_cnt", 200)
        self.qry_order = g_config.get_config("qry_order", 'desc')
        self.token = {}   # key为  refresh_token   val 为 临时token
        self.g_sublist = {}
        self.last_updated = datetime.now()
        self.get_access_token()
        self.get_subscribed_members()

    # 获取新的 access token
    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_access_token(self):

        for refresh_token in self.refresh_token:

            payload = {"refresh_token": refresh_token}

            resp = requests.request('POST', "https://api.n46.glastonr.net/v2/update_token", data=json.dumps(payload),
                                    headers=g_ngzk_headers, timeout=self.qry_timeout)
            # print(f"update_token res is {resp}")
            responseObject = json.loads(resp.text)
            if 'code' in responseObject and responseObject['code'] == 'unauthorized':
                continue
            token = responseObject['access_token']
            self.token[refresh_token] = token

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_subscribed_members(self) -> dict:
        res = {}
        for refresh_token in self.refresh_token:


            payload = {"refresh_token": refresh_token}
            auth_header = {'Authorization': 'Bearer ' + self.token[refresh_token]}
            headers = auth_header | g_ngzk_headers
            resp = requests.request('GET', "https://api.n46.glastonr.net/v2/groups?organization_id=1", data=json.dumps(payload),
                                    headers=headers,
                                    timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)
            # print(f'req groups: {responseObject}')
            for item in responseObject:
                if 'subscription' in item:
                    if 'state' in item['subscription']:
                        if item['name'] not in res:
                            res[item['name']] = NgzkMsgGroup(name=item['name'], id=item['id'], avatar=item['thumbnail'])
                        if self.token[refresh_token] not in res[item['name']].AvailableTokenDict:
                            res[item['name']].AvailableTokenDict[refresh_token] = self.token[refresh_token]
            # if item['name'] not in g_msg_signature:
            #     g_msg_signature[item['name']] = []


            for member_name in res:
                for refresh_token in self.refresh_token_mapping:
                    if member_name in refresh_token['member']:
                        res[member_name].AvailableTokenDict = {refresh_token['token']: self.token[refresh_token['token']]}

            self.g_sublist = res
        return res


    def refresh_expired_token(self):
        if (datetime.now() - self.last_updated) > timedelta(minutes=58):
            self.token = {}  # key为  refresh_token   val 为 临时token
            self.g_sublist = {}
            self.last_updated = datetime.now()
            self.get_access_token()
            self.get_subscribed_members()

    def get_available_token(self, member: str):
        self.refresh_expired_token()
        if member in self.g_sublist:
            return list(self.g_sublist[member].AvailableTokenDict.items())[0]

        return None, None

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_latest_msgs(self, member: str, updated_from=None):

        refresh_token, token = self.get_available_token(member)

        if refresh_token is None:
            print(f"failed to find available token for {member}")
            return None

        if updated_from is None:
            now_time = datetime.now()
            utc_offset = 8  # 时区转换  +8
            utc_time = now_time - timedelta(hours=utc_offset + self.qry_history_spread)
            updated_from = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        res = []
        payload = {"refresh_token": refresh_token}
        if member in self.g_sublist:
            auth_header = {'Authorization': 'Bearer ' + self.token[refresh_token]}
            headers = auth_header | g_ngzk_headers
            params = {

                "count": str(self.qry_history_cnt),  # 获取msg的数量
                # "created_from": updated_from,  # msg 最开始的时间. 2022-02-21T16:24:39Z
                "order": self.qry_order,  # asc正序；desc逆序；
                # "updated_from": updated_from  # msg的时间点，采用的是格林尼治时间，与显示时间相差（-8）小时。2022-02-21T16:00:00Z
            }

            resp = requests.request('GET',
                                    "https://api.n46.glastonr.net/v2/groups/" + str(
                                        self.g_sublist[member].Id) + "/timeline?" + urlencode(
                                        params), data=json.dumps(payload), headers=headers, timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)

            print(f"resp of get msg is {responseObject}")

            if 'code' in responseObject and responseObject['code'] == 'unauthorized':
                self.token = self.get_access_token()
                raise ValueError("need update token")

            if 'messages' in responseObject:
                res = responseObject['messages']
        return res


class SkzkMsgApi(object):
    refresh_token: dict
    token: dict
    qry_timeout: int
    qry_history_spread: int
    qry_history_cnt: int
    qry_order: str
    g_sublist: dict

    def __init__(self):
        self.refresh_token = g_config.get_config("refresh_token_s46", [])
        self.refresh_token_mapping = g_config.get_config("refresh_tokens_s46", [])
        self.qry_timeout = g_config.get_config("qry_timeout", 3)
        self.qry_history_spread = g_config.get_config("qry_history_spread", 24)
        self.qry_history_cnt = g_config.get_config("qry_history_cnt", 200)
        self.qry_order = g_config.get_config("qry_order", 'desc')
        self.token = {}   # key为  refresh_token   val 为 临时token
        self.g_sublist = {}
        self.last_updated = datetime.now()
        self.get_access_token()
        self.get_subscribed_members()

    # 获取新的 access token
    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_access_token(self):

        for refresh_token in self.refresh_token:

            payload = {"refresh_token": refresh_token}
            headers = {
                'Host': 'api.s46.glastonr.net',
                'Content-Type': 'application/json',
                'Connection': 'keep-alive',
                'Accept': '*/*',
                'X-Talk-App-ID': 'jp.co.sonymusic.communication.nogizaka 2.4',
                'User-Agent': 'Hot/1.6.00 (jp.co.sonymusic.communication.nogizaka; build:145; iOS 16.1.2) Alamofire/5.6.2',
                'Accept-Language': 'zh-Hans-CN;q=1.0, en-CN;q=0.9, ja-CN;q=0.8',
                'Accept-Encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
                'Content-Length': '56'
            }

            resp = requests.request('POST', "https://api.s46.glastonr.net/v2/update_token", data=json.dumps(payload),
                                    headers=g_skzk_headers, timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)
            if 'code' in responseObject and responseObject['code'] == 'unauthorized':
                continue
            token = responseObject['access_token']
            self.token[refresh_token] = token

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_subscribed_members(self) -> dict:
        res = {}
        for refresh_token in self.refresh_token:


            payload = {"refresh_token": refresh_token}
            auth_header = {'Authorization': 'Bearer ' + self.token[refresh_token]}
            headers = auth_header | g_skzk_headers
            resp = requests.request('GET', "https://api.s46.glastonr.net/v2/groups?organization_id=1", data=json.dumps(payload),
                                    headers=headers,
                                    timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)
            # print(f'skzk req groups: {responseObject}')
            for item in responseObject:
                if 'subscription' in item:
                    if 'state' in item['subscription'] and (
                            item['subscription']['state'] == 'active'):
                        if item['name'] not in res:
                            res[item['name']] = NgzkMsgGroup(name=item['name'], id=item['id'], avatar=item['thumbnail'])
                        if self.token[refresh_token] not in res[item['name']].AvailableTokenDict:
                            res[item['name']].AvailableTokenDict[refresh_token] = self.token[refresh_token]
            # if item['name'] not in g_msg_signature:
            #     g_msg_signature[item['name']] = []
            for member_name in res:
                for refresh_token in self.refresh_token_mapping:
                    if member_name in refresh_token['member']:
                        res[member_name].AvailableTokenDict = {refresh_token['token']: self.token[refresh_token['token']]}
            self.g_sublist = res
        return res


    def refresh_expired_token(self):
        if (datetime.now() - self.last_updated) > timedelta(minutes=58):
            self.token = {}  # key为  refresh_token   val 为 临时token
            self.g_sublist = {}
            self.last_updated = datetime.now()
            self.get_access_token()
            self.get_subscribed_members()

    def get_available_token(self, member: str):
        self.refresh_expired_token()
        if member in self.g_sublist:
            return list(self.g_sublist[member].AvailableTokenDict.items())[0]

        return None, None

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_latest_msgs(self, member: str, updated_from=None):

        refresh_token, token = self.get_available_token(member)

        if refresh_token is None:
            print(f"failed to find available token for {member}")
            return None

        if updated_from is None:
            now_time = datetime.now()
            utc_offset = 8  # 时区转换  +8
            utc_time = now_time - timedelta(hours=utc_offset + self.qry_history_spread)
            updated_from = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        res = []
        payload = {"refresh_token": refresh_token}
        if member in self.g_sublist:
            auth_header = {'Authorization': 'Bearer ' + self.token[refresh_token]}
            headers = auth_header | g_skzk_headers

            params = {

                "count": str(self.qry_history_cnt),  # 获取msg的数量
                # "created_from": updated_from,  # msg 最开始的时间. 2022-02-21T16:24:39Z
                "order": self.qry_order,  # asc正序；desc逆序；
                # "updated_from": updated_from  # msg的时间点，采用的是格林尼治时间，与显示时间相差（-8）小时。2022-02-21T16:00:00Z
            }

            resp = requests.request('GET',
                                    "https://api.s46.glastonr.net/v2/groups/" + str(
                                        self.g_sublist[member].Id) + "/timeline?" + urlencode(
                                        params), data=json.dumps(payload), headers=headers, timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)

            # print(f"resp of get msg is {responseObject}")

            if 'code' in responseObject and responseObject['code'] == 'unauthorized':
                self.token = self.get_access_token()
                raise ValueError("need update token")

            if 'messages' in responseObject:
                res = responseObject['messages']
        return res

class HntzkMsgApi(object):
    refresh_token: dict
    token: dict
    qry_timeout: int
    qry_history_spread: int
    qry_history_cnt: int
    qry_order: str
    g_sublist: dict

    def __init__(self):
        self.refresh_token = g_config.get_config("refresh_token_h46", [])
        self.refresh_token_mapping = g_config.get_config("refresh_tokens_h46", [])
        self.qry_timeout = g_config.get_config("qry_timeout", 3)
        self.qry_history_spread = g_config.get_config("qry_history_spread", 24)
        self.qry_history_cnt = g_config.get_config("qry_history_cnt", 200)
        self.qry_order = g_config.get_config("qry_order", 'desc')
        self.token = {}   # key为  refresh_token   val 为 临时token
        self.g_sublist = {}
        self.last_updated = datetime.now()
        self.get_access_token()
        self.get_subscribed_members()

    # 获取新的 access token
    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_access_token(self):

        for refresh_token in self.refresh_token:

            payload = {"refresh_token": refresh_token}
            headers = {
                'Host': 'api.kh.glastonr.net',
                'Content-Type': 'application/json',
                'Connection': 'keep-alive',
                'Accept': '*/*',
                'X-Talk-App-ID': 'jp.co.sonymusic.communication.nogizaka 2.4',
                'User-Agent': 'Hot/1.6.00 (jp.co.sonymusic.communication.nogizaka; build:145; iOS 16.1.2) Alamofire/5.6.2',
                'Accept-Language': 'zh-Hans-CN;q=1.0, en-CN;q=0.9, ja-CN;q=0.8',
                'Accept-Encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
                'Content-Length': '56'
            }

            resp = requests.request('POST', "https://api.kh.glastonr.net/v2/update_token", data=json.dumps(payload),
                                    headers=g_htzk_headers, timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)
            if 'code' in responseObject and responseObject['code'] == 'unauthorized':
                continue
            token = responseObject['access_token']
            self.token[refresh_token] = token

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_subscribed_members(self) -> dict:
        res = {}
        for refresh_token in self.refresh_token:


            payload = {"refresh_token": refresh_token}
            auth_header = {'Authorization': 'Bearer ' + self.token[refresh_token]}
            headers = auth_header | g_htzk_headers
            resp = requests.request('GET', "https://api.kh.glastonr.net/v2/groups?organization_id=1", data=json.dumps(payload),
                                    headers=headers,
                                    timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)
            # print(responseObject)
            # print(f'req groups: {responseObject}')
            for item in responseObject:
                if 'subscription' in item:
                    if 'state' in item['subscription'] and (
                            item['subscription']['state'] == 'active'):
                        if item['name'] not in res:
                            res[item['name']] = NgzkMsgGroup(name=item['name'], id=item['id'], avatar=item['thumbnail'])
                        if self.token[refresh_token] not in res[item['name']].AvailableTokenDict:
                            res[item['name']].AvailableTokenDict[refresh_token] = self.token[refresh_token]
            # if item['name'] not in g_msg_signature:
            #     g_msg_signature[item['name']] = []

            for member_name in res:
                for refresh_token in self.refresh_token_mapping:
                    if member_name in refresh_token['member']:
                        res[member_name].AvailableTokenDict = {refresh_token['token']: self.token[refresh_token['token']]}

            self.g_sublist = res
        return res


    def refresh_expired_token(self):
        if (datetime.now() - self.last_updated) > timedelta(minutes=58):
            self.token = {}  # key为  refresh_token   val 为 临时token
            self.g_sublist = {}
            self.last_updated = datetime.now()
            self.get_access_token()
            self.get_subscribed_members()

    def get_available_token(self, member: str):
        self.refresh_expired_token()
        if member in self.g_sublist:
            return list(self.g_sublist[member].AvailableTokenDict.items())[0]

        return None, None

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_latest_msgs(self, member: str, updated_from=None):

        refresh_token, token = self.get_available_token(member)

        if refresh_token is None:
            print(f"failed to find available token for {member}")
            return None

        if updated_from is None:
            now_time = datetime.now()
            utc_offset = 8  # 时区转换  +8
            utc_time = now_time - timedelta(hours=utc_offset + self.qry_history_spread)
            updated_from = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        res = []
        payload = {"refresh_token": refresh_token}
        if member in self.g_sublist:
            auth_header = {'Authorization': 'Bearer ' + self.token[refresh_token]}
            headers = auth_header | g_htzk_headers

            params = {

                "count": str(self.qry_history_cnt),  # 获取msg的数量
                # "created_from": updated_from,  # msg 最开始的时间. 2022-02-21T16:24:39Z
                "order": self.qry_order,  # asc正序；desc逆序；
                # "updated_from": updated_from  # msg的时间点，采用的是格林尼治时间，与显示时间相差（-8）小时。2022-02-21T16:00:00Z
            }

            resp = requests.request('GET',
                                    "https://api.kh.glastonr.net/v2/groups/" + str(
                                        self.g_sublist[member].Id) + "/timeline?" + urlencode(
                                        params), data=json.dumps(payload), headers=headers, timeout=self.qry_timeout)

            responseObject = json.loads(resp.text)

            # print(f"resp of get msg is {responseObject}")

            if 'code' in responseObject and responseObject['code'] == 'unauthorized':
                self.token = self.get_access_token()
                raise ValueError("need update token")

            if 'messages' in responseObject:
                res = responseObject['messages']
        return res


class N46BlogApi(object):
    reqUrl: str

    def __init__(self):
        self.reqUrl = 'https://www.nogizaka46.com/s/n46/api/list/blog?ima=5652&rw=32&st=0&callback=res'

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_latest_blogs(self):
        res = requests.request('get', self.reqUrl, timeout=10)
        res_len = len(res.text)
        res_str = res.text[4:res_len - 2]
        res_json_obj = json.loads(res_str)
        return res_json_obj['data']


class S46BlogApi(object):
    reqUrl: str

    def __init__(self):
        self.reqUrl = 'https://www.sakurazaka46.com/s/s46app/api/json/diary?cd=blog'

    @retry(wait=wait_random(min=2, max=5), stop=stop_after_attempt(3), reraise=True)
    def get_latest_blogs(self):
        res = requests.request('get', self.reqUrl, timeout=10)
        res_str = res.text
        res_json_obj = json.loads(res_str)
        blogs = res_json_obj['blog']
        return blogs


g_blog_api = N46BlogApi()
g_msg_api = NgzkMsgApi()
g_s46_blog_api = S46BlogApi()
g_s46_msg_api = SkzkMsgApi()
g_h46_msg_api = HntzkMsgApi()
