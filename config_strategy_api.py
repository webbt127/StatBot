"""
    API Documentation
    https://github.com/alpacahq/alpaca-trade-api-python
    
"""

# API Imports
from alpaca_trade_api import REST, Stream

# CONFIG
mode = "test"
timeframe = 60
kline_limit = 200
z_score_window = 21

# LIVE API
api_key_mainnet = ""
api_secret_mainnet = ""

# TEST API
api_key_testnet = "PKX9QLYDX6CFM5FU0WSH"
api_secret_testnet = "v8CtBo4qMYj2PJcbiyXxig1hzMIh7deRHdyK3Ylb"

# SELECTED API
api_key = api_key_testnet if mode == "test" else api_key_mainnet
api_secret = api_secret_testnet if mode == "test" else api_secret_mainnet

# SELECTED URL
api_url = "https://paper-api.alpaca.markets" if mode == "test" else "https://api.alpaca.markets"

# SESSION Activation
session = REST(api_url)

# # Web Socket Connection
# subs = [
#     "candle.1.BTCUSDT"
# ]
# ws = WebSocket(
#     "wss://stream-testnet.bybit.com/realtime_public",
#     subscriptions=subs
# )
#
# while True:
#     data = ws.fetch(subs[0])
#     if data:
#         print(data)
