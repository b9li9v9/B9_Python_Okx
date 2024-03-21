# -*- coding: utf-8 -*-

import json
import asyncio
import time
from datetime import datetime
from B9_Httpx import HClient
from B9_Logger import Logger
from B9_AWsClient import AWsClient
from B9_UserConfig import UserConfig
from B9_AQueuePool import AQueuePool
from B9_CoroutineMonitor import CoroutineMonitor


# 公共频道
async def public_producer(ws,aqueuepool):

    Public_BOOM = 0
    aqueuepool.pubqueue = asyncio.Queue()
    PublicChannels = [{
        "channel": "trades",
        "instId": "BTC-USDT"
    }]

    while True:
        try:  # 无限连接
            await ws.start()
            if ws.websocket:
                await ws.subscribe(PublicChannels)  # 订阅
                await Logger.write_log("Public Enqueue Loop Run...")
                while True:
                    try:
                        message = await asyncio.wait_for(ws.websocket.recv(), timeout=5)  # 设置超时时间为5秒
                        await aqueuepool.putQueue(aqueuepool.pubqueue,message)  # 消息入队
                    except asyncio.TimeoutError:  # 处理超时异常
                        await Logger.write_log("Business ERROR MessageQueue Timeout occurred!!")
                        break  # 超时时跳出循环
                    except Exception as e:
                        await Logger.write_log(f"Public ERROR occurred: {e}")
                        break  # 处理任何异常时跳出循环
        finally:
            await aqueuepool.clearQueue(aqueuepool.pubqueue)  # 清空队列
            await ws.stop()  # 清理退出
            Public_BOOM += 1  # 断连记数
            await Logger.write_log(f"Public BOOM -> {Public_BOOM} Restart !!!")


# 私有频道
async def private_producer(ws, CoroutineMonitor, aqueuepool):

    Private_BOOM = 0
    aqueuepool.priqueue = asyncio.Queue()
    PrivateChannels = [{
        "channel": "orders",
        "instType": "SWAP",
        # "instFamily": "BTC-USD",
        "instId": "BTC-USDT-SWAP"
    }]

    while True:
        try:  # 无限连接
            await ws.start()
            if ws.websocket:
                await ws.login()  # 私有登录 这里会asyncio.sleep(3)  速率可以调整。
                await ws.subscribe(PrivateChannels)  # 订阅
                await Logger.write_log("Private Enqueue Loop Run...")
                while True:
                    try:
                        message = await ws.websocket.recv()  # 设置超时时间为5秒
                        await aqueuepool.putQueue(aqueuepool.priqueue, message)  # 消息入队
                    except Exception as e:
                        await Logger.write_log(f"Private ERROR occurred: {e}")
                        break  # 处理异常时跳出循环
                    CoroutineMonitor.Broadcast('private task') # 这个要有接收信息才会监控 心跳刚好和这个同速 但这个监控不准
        finally:
            await aqueuepool.clearQueue(aqueuepool.priqueue)  # 清空队列
            await ws.stop()  # 清理退出
            Private_BOOM += 1  # 断连记数
            await Logger.write_log(f"Private BOOM -> {Private_BOOM} Restart !!!")


# 私有频道心跳
async def private_timer(interval, priws):
    while True:
        await asyncio.sleep(interval)
        await priws.websocket.send('ping')


# 业务频道
async def business_producer(ws, CoroutineMonitor, aqueuepool):

    Business_BOOM = 0
    aqueuepool.busqueue = asyncio.Queue()
    BusinessChannels = [{
        "channel": "candle1s",
        "instId": "BTC-USDT"
    }]

    while True:
        try:  # 无限连接
            await ws.start()
            if ws.websocket:
                await ws.subscribe(BusinessChannels)  # 订阅
                await Logger.write_log("Business Enqueue Loop Run...")
                while True:
                    try:
                        message = await asyncio.wait_for(ws.websocket.recv(), timeout=5)  # 设置超时时间为5秒
                        await aqueuepool.putQueue(aqueuepool.busqueue,message)  # 消息入队
                    except asyncio.TimeoutError:  # 处理超时异常
                        await Logger.write_log("Business ERROR MessageQueue Timeout occurred!!")
                        break  # 超时时跳出循环
                    except Exception as e:
                        await Logger.write_log(f"Business ERROR occurred: {e}")
                        break  # 处理任何异常时跳出循环
                    CoroutineMonitor.Broadcast('business task')
        finally:
            await aqueuepool.clearQueue(aqueuepool.busqueue)  # 清空队列
            await ws.stop()  # 清理退出
            Business_BOOM += 1  # 断连记数
            await Logger.write_log(f"Business BOOM -> {Business_BOOM} Restart !!!")

# 业务数据过滤器
async def business_clan(uc,priws,aqueuepool):
    if not aqueuepool.busqueue.empty():
        # 等待获取异步队列数据
        message = await aqueuepool.busqueue.get()
        if priws.websocket and priws.LoginStatus and priws.SubscribeStatus:
            # 只清洗符合结构的数据，不符合的全部进日志就行。
            try:
                # 处理数据
                parsed_data = json.loads(message)

                # 取值
                data_list = parsed_data['data'][0]
                # 初始化时间戳
                try:
                    timestamp = int(data_list[0])
                except ValueError:
                    await Logger.write_log("Error: Failed to convert timestamp to integer.")
                    timestamp = None
                    raise

                # 初始化金额等数据
                values = []
                for v in data_list[1:]:
                    try:
                        # 使用 Decimal 类型来表示金额等数据
                        value = float(v)
                        values.append(value)
                    except ValueError:
                        await Logger.write_log(f"Error: Failed to convert {v} to Decimal.")
                        values.append(None)  # 添加 None 表示转换失败
                        raise

                # 将时间戳转换为 datetime 对象
                dt_object = datetime.fromtimestamp(timestamp / 1000)  # 注意除以1000将毫秒转换为秒
                # 格式化日期时间字符串
                formatted_datetime = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                # print("Timestamp:", formatted_datetime)
                # print("Values:", values)

                item = {}
                item['channel'] = parsed_data['arg']['channel']
                item['instId'] = parsed_data['arg']['instId']
                item['Timestamp'] = timestamp
                item['open'] = values[0]
                item['high'] = values[1]
                item['low'] = values[2]
                item['close'] = values[3]
                item['vol'] = values[4]
                item['volCcy'] = values[5]
                item['volCcyQuote'] = values[6]
                item['confirm'] = values[7]
                # 传递进策略区
                await handle(uc, priws, item, 'bus')
            except:
                await Logger.write_log(message)
                print(message)
        else:
            print(f"private ws login subscribe must right {message}")
    else:
        await asyncio.sleep(0)

# 私有数据过滤器
async def private_clan(uc,priws,aqueuepool):
    if not aqueuepool.priqueue.empty():
        # 等待获取异步队列数据
        message = await aqueuepool.priqueue.get()
        if priws.websocket and priws.LoginStatus and priws.SubscribeStatus:
            if message != 'pong':
                await Logger.write_log(f"{message}")
                await handle(uc, priws, message, 'pri')
            else:
                await handle(uc, priws, message, 'pri')
        else:
            print(f"private ws login subscribe must right {message}")
    else:
        await asyncio.sleep(0)

# 消费者
async def consumer(uc, priws, CoroutineMonitor, aqueuepool):
    # 传递给过滤器
    while True:
        await business_clan(uc,priws,aqueuepool)
        await private_clan(uc,priws,aqueuepool)
        CoroutineMonitor.Broadcast('consumer task')


# 策略区
async def handle(uc, priws, data, datatype):
    if datatype == 'bus':
        if not uc.TradeSwitch:
            print('交易开关未打开、请审慎操作')
        else:

            # 将时间戳转换为 datetime 对象
            dt_object = datetime.fromtimestamp(data['Timestamp'] / 1000)  # 注意除以1000将毫秒转换为秒
            # 格式化日期时间字符串
            formatted_datetime = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            # 比较本地和服务器时间、打印行情数据
            print(f"{datetime.fromtimestamp(int(time.time()))} {formatted_datetime} handle message: {data}")

            # 交易逻辑
            if data['close'] <= 67710.0 and not uc.Tradeing:
                trademes = json.dumps({
                    "id": "indan",
                    "op": "order",
                    "args": [{
                        "side": "buy",
                        "posSide": "long",
                        "instId": "BTC-USDT-SWAP",
                        "tdMode": "isolated",
                        "ordType": "market",
                        "sz": "1"
                    }]
                })
                await priws.websocket.send(trademes)
                print('buy')
                uc.Tradeing = True
            elif data['close'] >= 67780.0 and uc.Tradeing:
                trademes = json.dumps({
                    "id": "outdan",
                    "op": "order",
                    "args": [{
                        "side": "sell",
                        "posSide": "long",
                        "instId": "BTC-USDT-SWAP",
                        "tdMode": "isolated",
                        "ordType": "market",
                        "sz": "1"
                    }]
                })
                await priws.websocket.send(trademes)
                print('sell')
                uc.Tradeing = False
    elif datatype == 'pri':
        print(str(datetime.fromtimestamp(int(time.time()))),data)
    else:
        raise


# 账户初始化
async def SetAccount(prihc):
    # 该函数用于init账户设置
    try:
        tasks1 = asyncio.create_task(prihc._request_without_params('GET', r"/api/v5/account/balance"))  # 获取账户中所有、或指定的资产余额
        tasks2 = asyncio.create_task(prihc._request_without_params('GET', r"/api/v5/account/positions"))  # 查看BTC-USDT的持仓信息
        tasks3 = asyncio.create_task(prihc._request_without_params('GET', r"/api/v5/account/config"))  # 查看当前账户的配置信息

        tasks4 = asyncio.create_task(prihc._request_with_params('POST', r"/api/v5/account/set-position-mode",  # 持仓方式long_short_mode：开平仓模式 net_mode：买卖模式仅适用交割/永续
                                                                {'posMode': 'long_short_mode'}))

        tasks5 = asyncio.create_task(prihc._request_with_params('POST', r"/api/v5/account/set-leverage",  # 持仓杠杆设置
                                                                {
                                                                    "instId": "BTC-USDT-SWAP",
                                                                    "lever": "100",
                                                                    "posSide": "long",
                                                                    "mgnMode": "isolated"
                                                                }))
        tasks6 = asyncio.create_task(prihc._request_with_params('POST', f"/api/v5/account/set-leverage",
                                                                {
                                                                    "instId": "BTC-USDT-SWAP",
                                                                    "lever": "100",
                                                                    "posSide": "short",
                                                                    "mgnMode": "isolated"
                                                                }))

        tasks7 = asyncio.create_task(prihc._request_without_params("GET",r"/api/v5/account/max-size?instId=BTC-USDT-SWAP&tdMode=isolated"))  # 最大交易上线量
        tasks8 = asyncio.create_task(prihc._request_without_params("GET",r"/api/v5/account/max-avail-size?instId=BTC-USDT-SWAP&tdMode=isolated"))
        # 查看BTC-USDT的持仓信息
        tasks9 = asyncio.create_task(prihc._request_without_params("GET", r"/api/v5/account/positions?instId=BTC-USDT-SWAP"))  # 持仓详情

        # 并发执行任务
        results = await asyncio.gather(tasks1, tasks2, tasks3, tasks4, tasks5, tasks6, tasks7, tasks8, tasks9)

        # 写入日志
        for result in results:
            await Logger.write_log(result)

    except Exception as e:
        await Logger.write_log(f"An error occurred:  {e}")
        raise 'httpx request error'

    finally:
        # 关闭客户端
        await prihc.client.aclose()


# 启动函数
async def main():
    # 清空日志
    await Logger.clear_log()

    # httpx客户端 私
    PriHC = HClient(api_key=UserConfig.apiKey, api_secret_key=UserConfig.secretKey, passphrase=UserConfig.passphrase)
    # 异步 Ws客户端 公、私、业务
    # PubWsC = AWsClient(url=UC.PublicUrl)
    PriWsC = AWsClient(url=UserConfig.PrivateUrl,apiKey=UserConfig.apiKey,passphrase=UserConfig.passphrase,secretKey=UserConfig.secretKey)
    BusWsC = AWsClient(url=UserConfig.BusinessUrl)

    # 协程任务监控
    CoroutineMonitor_task = asyncio.create_task(CoroutineMonitor.start(10))

    # 封装任务
    # Public_WsC_task = asyncio.create_task(public_producer(PubWsC,AQueuePool))
    Private_WsC_task = asyncio.create_task(private_producer(PriWsC, CoroutineMonitor, AQueuePool))
    Business_WsC_task = asyncio.create_task(business_producer(BusWsC, CoroutineMonitor, AQueuePool))
    Consumer_Handel_task = asyncio.create_task(consumer(UserConfig, PriWsC, CoroutineMonitor, AQueuePool))  # 策略区
    private_timer_task = asyncio.create_task(private_timer(10,PriWsC)) # 私有客户端心跳

    # 阻塞 账户初始
    await SetAccount(PriHC)

    # 并发
    # await Public_WsC_task
    await Private_WsC_task
    await Business_WsC_task
    await Consumer_Handel_task
    await private_timer_task
    await CoroutineMonitor_task

if __name__ == "__main__":
    asyncio.run(main())

