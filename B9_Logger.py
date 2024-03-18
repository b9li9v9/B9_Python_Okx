from B9_UserConfig import UserConfig
from datetime import datetime,time
import time
import aiofiles


class Logger():
    @classmethod
    async def write_log(cls,message):
        times = str(datetime.fromtimestamp(int(time.time())))
        print(f"Logger: {times} {message}")
        async with aiofiles.open(UserConfig.LogFilePath, mode='a',encoding='utf-8') as f:
            message = str(message)
            logtext = times + ' ' + message + '\n'
            await f.write(logtext)

    @classmethod
    async def clear_log(cls):
        with open(UserConfig.LogFilePath, 'w',encoding='utf-8') as file:
            file.truncate(0)