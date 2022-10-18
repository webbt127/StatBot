"""
    API Documentation
    https://bybit-exchange.github.io/docs/linear/#t-introduction
"""

# API Imports
from alpaca_trade_api import REST, Stream

# CONFIG VARIABLES
mode = "test"
ticker_1 = "MATICUSDT"
ticker_2 = "STXUSDT"
signal_positive_ticker = ticker_2
signal_negative_ticker = ticker_1
rounding_ticker_1 = 2
rounding_ticker_2 = 2
quantity_rounding_ticker_1 = 0
quantity_rounding_ticker_2 = 0

limit_order_basis = True # will ensure positions (except for Close) will be placed on limit basis

tradeable_capital_usdt = 500 # total tradeable capital to be split between both pairs
stop_loss_fail_safe = 0.30 # stop loss at market order in case of drastic event
signal_trigger_thresh = 1.1 # z-score threshold which determines trade (must be above zero)

timeframe = 60 # make sure matches your strategy
kline_limit = 10000 # make sure matches your strategy
z_score_window = 21 # make sure matches your strategy

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
ws_public_url = "wss://paper-api.alpaca.markets/stream" if mode == "test" else "wss://api.alpaca.markets/stream"

# SESSION Activation
session_public = REST(api_url)
session_private = REST(api_url, api_key=api_key, api_secret=api_secret)
