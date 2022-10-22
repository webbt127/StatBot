from alpaca_trade_api import REST, Stream

# LIVE API
api_key_mainnet = ""
api_secret_mainnet = ""

# TEST API
api_key_testnet = "PKX9QLYDX6CFM5FU0WSH"
api_secret_testnet = "v8CtBo4qMYj2PJcbiyXxig1hzMIh7deRHdyK3Ylb"

# SELECTED API
api_key = api_key_testnet
api_secret = api_secret_testnet 

# SELECTED URL
api_url = "https://paper-api.alpaca.markets"

# CONFIG
class position:
	def __init__(self):
    		self.symbol = ""
		

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

		self.limit_order_basis = True # will ensure positions (except for Close) will be placed on limit basis

		self.tradeable_capital_usdt = 500 # total tradeable capital to be split between both pairs
		self.stop_loss_fail_safe = 0.30 # stop loss at market order in case of drastic event
		self.signal_trigger_thresh = 1.1 # z-score threshold which determines trade (must be above zero)
	
		self.timeframe = 60
		self.kline_limit = 10000
		self.z_score_window = 21
		self.max_positions = 10
		self.search_limit = 10000
