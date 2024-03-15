"""
实盘
WebSocket公共频道：wss://ws.okx.com:8443/ws/v5/public
WebSocket私有频道：wss://ws.okx.com:8443/ws/v5/private
WebSocket业务频道：wss://ws.okx.com:8443/ws/v5/business
模拟盘
WebSocket公共频道：wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999
WebSocket私有频道：wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999
WebSocket业务频道：wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999
"""
# 用户面板，所有参数在这里设置
class UserConfig:

        PublicUrl = "wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999"
        PrivateUrl = "wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999"
        BusinessUrl = "wss://ws.okx.com:8443/ws/v5/business"
        apiKey = ""
        passphrase = ""
        secretKey = ""
        LogFilePath = 'B9_OkxDebug.log'  # 日志路径

        useServerTime = True
        BOOM = 0 # 断线重连次数
        TradeSwitch = True  # 交易开关
        Tradeing = False  # 交易信号
