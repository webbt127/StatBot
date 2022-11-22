from alpaca_trade_api import REST, Stream
from pathlib import Path

# LIVE API
api_key_mainnet = ""
api_secret_mainnet = ""

# TEST API
api_key_testnet = "PKAFGQA2GG10RZ5BNX23"
api_secret_testnet = "hgOWFBG8WylBZ8EwP8i9KSU1FXNu7vFZWlTUgfa0"

# SELECTED API
api_key = api_key_testnet
api_secret = api_secret_testnet 

# SELECTED URL
api_url = "https://paper-api.alpaca.markets"

# CONFIG
class position:
	def __init__(self):
    		self.symbol = ""
		
class assets:
	def __init__(self):
    		pass


class config:
	def __init__(self):
    
		self.ticker_1 = "MATICUSDT"
		self.ticker_2 = "STXUSDT"
		self.signal_positive_ticker = self.ticker_2
		self.signal_negative_ticker = self.ticker_1
		self.rounding_ticker_1 = 2
		self.rounding_ticker_2 = 2
		self.quantity_rounding_ticker_1 = 0
		self.quantity_rounding_ticker_2 = 0
		self.price_rounding = 2

		self.limit_order_basis = True # will ensure positions (except for Close) will be placed on limit basis
		self.stop_loss_fail_safe = 0.30 # stop loss at market order in case of drastic event
	
		self.timeframe = 60
		self.kline_limit = 2000
		self.z_score_window = 21
		self.max_positions = 10
		self.search_limit = 10000
		self.capital_per_trade = 1000
		self.test_set = 500
		self.bollinger_length = 21
		self.min_zero_crosses = 5
		self.pairs_path = Path("cointegrated_pairs.csv")
		self.get_new_pairs = True
		self.telegram_chat_id = '1993028760'
		self.telegram_api_key = '5558182464:AAE-d-6mNR8zNr2gxW-QxicXIbRCmB6vi6E'

global api
api = config()
api.session = REST(api_key, api_secret, api_url)

global asset_list
asset_list = assets()

global coint_pair_list
global included_list
coint_pair_list = []
included_list = []
