import json

import httpx

import B9_HttpxUtils, B9_HttpxExceptions


class HClient(object):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.flag = flag
        self.client = httpx.Client(base_url='https://www.okx.com', http2=True)

    async def _request(self, method, request_path, params):
        if method == "GET":
            request_path = request_path + B9_HttpxUtils.parse_params_to_str(params)
        timestamp = B9_HttpxUtils.get_timestamp()
        if self.use_server_time:
            timestamp = await self._get_timestamp()
        body = json.dumps(params) if method == "POST" else ""
        sign = B9_HttpxUtils.sign(B9_HttpxUtils.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = B9_HttpxUtils.get_header(self.API_KEY, sign, timestamp, self.PASSPHRASE, self.flag)
        response = None
        if method == "GET":
            response = self.client.get(request_path, headers=header)
        elif method == "POST":
            response = self.client.post(request_path, data=body, headers=header)
        if not str(response.status_code).startswith('2'):
            raise B9_HttpxExceptions.OkxAPIException(response)
        return response.json()

    async def _request_without_params(self, method, request_path):
        return await self._request(method, request_path, {})

    async def _request_with_params(self, method, request_path, params):
        return await self._request(method, request_path, params)

    async def _get_timestamp(self):
        request_path = 'https://www.okx.com' + '/api/v5/public/time'
        response = self.client.get(request_path)
        if response.status_code == 200:
            return response.json()['data'][0]['ts']
        else:
            return ""
