import asyncio
import time
from datetime import datetime


class CoroutineMonitor:
    Statu = True
    CorosPool = {}

    # 注册
    @classmethod
    def register(cls, coros):
        cls.CorosPool[coros] = False

    # 取消
    @classmethod
    def unregister(cls, name_to_remove):
        if name_to_remove in cls.CorosPool:
            del cls.CorosPool[name_to_remove]
            print(f"已注销名为: {name_to_remove} 的协程")
        else:
            print(f"未找到名为: {name_to_remove} 的协程")

    # 启动
    @classmethod
    async def start(cls, interval):
        while cls.Statu:
            for coros in cls.CorosPool:
                cls.CorosPool[coros] = not cls.CorosPool[coros]
            await asyncio.sleep(interval)

    # 关闭
    @classmethod
    def shutdown(cls):
        cls.Statu = False

    # 广播
    @classmethod
    def Broadcast(cls, corosName):
        if corosName not in cls.CorosPool:
            cls.CorosPool[corosName] = True

        if cls.CorosPool[corosName]:
            print(f"{datetime.now()} {corosName} 协程正在运行")
            cls.CorosPool[corosName] = False
