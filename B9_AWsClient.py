import json
import base64
import hmac
import time
import requests
import ssl
import certifi
import websockets

# Asynchronous  WebSocket client
class AWsClient:

    def __init__(self, url, useServerTime=False, apiKey=None, passphrase=None, secretKey=None):
        # 初始化 WebSocket 私有频道对象
        self.url = url  # WebSocket 服务器的 URL 地址

        self.apiKey = apiKey  # API 密钥
        self.passphrase = passphrase  # Passphrase
        self.secretKey = secretKey  # Secret Key

        self.ssl_context = ssl.create_default_context()  # 创建默认的 SSL 上下文
        self.ssl_context.load_verify_locations(certifi.where())  # 加载证书路径

        self.websocket = None # ws连接对象
        self.LoginStatus = False #登录状态 待定。
        self.SubscribeStatus = False # 订阅状态

        self.useServerTime = useServerTime  # 是否使用服务器时间

    # 启动 WebSocket 连接
    async def start(self):
        print("WebSocket Start Activate...")
        try:
            self.websocket = await websockets.connect(self.url, ssl=self.ssl_context)  # 连接到 WebSocket 服务器
            print("WebSocket Connection established.")  # 记录 WebSocket 连接已建立
            return self.websocket  # 返回 WebSocket 连接对象
        except Exception as e:
            print(f"Error Connecting to WebSocket: {e}")  # 记录连接 WebSocket 时出错的异常信息
            return None

    # 停止 WebSocket 连接
    async def stop(self):
        print("WebSocket Stop Deactivate...")
        if self.websocket:  # 如果 WebSocket 连接对象存在
            await self.websocket.close()  # 关闭 WebSocket 连接
            self.websocket = None  # 将 WebSocket 连接对象设为 None，表示连接已关闭
        else:
            print("Websocket Stop Failed Ws Is None.")

    # 登录 WebSocketServer 连接
    async def login(self):
        print("WebSocket Login Activate...")
        if self.websocket:
            loginPayload = await self.CheckLogin(
                useServerTime=self.useServerTime,
                apiKey=self.apiKey,
                passphrase=self.passphrase,
                secretKey=self.secretKey
            )
            await self.websocket.send(loginPayload)
            # await asyncio.sleep(3)
            self.LoginStatus = True
            print(f"Login established.")
        else:
            print("!! ws must connection login error")

    # 订阅私有频道
    async def subscribe(self, params):
        print("WebSocket Subscribe Activate...")
        if self.websocket:
            payload = json.dumps({
                "op": "subscribe",
                "args": params
            })
            await self.websocket.send(payload)
            print(f"Subscribe: {payload}")
            self.SubscribeStatus = True
        else:
            print("!! ws must connection subscribe error")

    # 取消订阅私有频道
    async def unsubscribe(self, params):
        print("WebSocket UnSubscribe Deactivate...")
        payload = json.dumps({
            "op": "unsubscribe",
            "args": params
        })
        await self.websocket.send(payload)
        print(f"unsubscribe: {payload}")
        self.SubscribeStatus = False

    # 初始化登录参数
    async def CheckLogin(self,useServerTime: bool, apiKey, passphrase, secretKey):
        # 这个函数

        # 获取本地时间戳
        async def getLocalTime():
            return int(time.time())

        # 获取服务器时间
        async def getServerTime():
            url = "https://www.okx.com/api/v5/public/time"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()['data'][0]['ts']
            else:
                return ""

        # 获取时间戳
        timestamp = await getLocalTime()
        # 如果使用服务器时间，则获取服务器时间作为时间戳
        if useServerTime:
            timestamp = await getServerTime()

        # 构造待签名的消息
        message = str(timestamp) + 'GET' + '/users/self/verify'
        # 使用 HMAC-SHA256 算法生成签名
        mac = hmac.new(bytes(secretKey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        sign = base64.b64encode(d)
        # 构造登录参数并转换为 JSON 字符串
        arg = {"apiKey": apiKey, "passphrase": passphrase, "timestamp": timestamp, "sign": sign.decode("utf-8")}
        payload = {"op": "login", "args": [arg]}
        return json.dumps(payload)

