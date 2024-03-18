import asyncio


class AQueuePool:
    # 加入队列
    @classmethod
    async def putQueue(cls, queue, message):
        await queue.put(message)

    # 清空队列
    @classmethod
    async def clearQueue(cls,queue):
        print("WebSocket Clear MessageQueue...")
        queue = asyncio.Queue()