from alpaca_trade_api import REST, Stream

# LIVE API
api_key_mainnet = ""
api_secret_mainnet = ""

# TEST API
api_key_testnet = "PK1LUNWAW283CCMU2ID7"
api_secret_testnet = "HPGm4D3ie963AUIqRrMo4ikhy0sw2AfgwFZTojNa"

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

		self.tradable_capital_usdt = 1000 # total tradeable capital to be split between both pairs
		self.stop_loss_fail_safe = 0.30 # stop loss at market order in case of drastic event
		self.signal_trigger_thresh = 0.5 # z-score threshold which determines trade (must be above zero)
	
		self.timeframe = 60
		self.kline_limit = 10000
		self.z_score_window = 21
		self.max_positions = 10
		self.search_limit = 10000
		self.get_new_history = False
		self.capital_per_trade = 1000
		self.test_set = 1100

global api
api = config()
api.session = REST(api_key, api_secret, api_url)

global asset_list
asset_list = assets()

global coint_pair_list
global included_list
coint_pair_list = []
included_list = []
