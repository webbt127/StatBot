import time
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import pandas as pd
import math
import threading
import yfinance as yf
from config_strategy_api import *
from func_cointegration import *
from alive_progress import alive_bar
import logging as lg
from joblib import Parallel, delayed, parallel_backend
#from pbar_parallel import PBarParallel, delayed
from yahoo_fin import stock_info
from alpaca_trade_api.rest import TimeFrame
import datetime

def exit_handler():
	message = 'Exception Occurred'
	send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
	return

class position_list:
	def __init__(self):
		self.lock = Lock()
		self.positions = pd.DataFrame(columns=['sym_1', 'sym_2', 'p_value', 't_value', 'c_value', 'hedge_ratio', 'zero_crossings', 'index', 'hedge_ratio'])

def cancel_orders():
	try:
		api.session.cancel_all_orders()
	except Exception as e:
		lg.info("Unable To Cancel All Orders")

def wait_for_market_open():
	clock = api.session.get_clock()
	if not clock.is_open:
		time_to_open = clock.next_open - clock.timestamp
		sleep_time = round(time_to_open.total_seconds())
		time.sleep(sleep_time)
		cancel_orders()
	return clock

def get_orderbook(asset):

	asset.orderbook = Orderbook()
	asset.latest_quote = api.session.get_latest_quote(asset.symbol)
	asset.orderbook.ap = getattr(asset.latest_quote, 'ap')
	asset.orderbook.bp = getattr(asset.latest_quote, 'bp')
	return asset


def get_price_history():

    # Get prices and store in DataFrame
	price_history_dict = {}
	Parallel(n_jobs=8, verbose=10, prefer="threads")(delayed(price_history_execution)(asset) for asset in asset_list.symbols)	
    # Return output
	return asset_list

def price_history_execution(asset):
	asset.klines = None
	timeframe = TimeFrame.Hour
	get_price_klines(asset, timeframe, api.kline_limit)
	#if asset.klines is not None:
		#lg.info("Successfully Stored Data For %s!" % asset.symbol)
	if asset.klines is None:
		asset_list.symbols.remove(asset)
		lg.info("Unable To Store Data For %s! Removed From Asset List" % asset.symbol)
	return asset, asset_list

def get_start_time(api):
	time_start_date = 0
	if api.timeframe == 60:
		time_start_date = datetime.datetime.now() - datetime.timedelta(hours=api.kline_limit)
	if api.timeframe == "D":
		time_start_date = datetime.datetime.now() - datetime.timedelta(days=kline_limit)
	time_start = time_start_date.isoformat("T") + "Z"
	return time_start

# Get historical prices (klines)
def get_price_klines(asset, timeframe, klines):

	asset.klines = None
	start_time = get_start_time(api)
	try:
		asset.klines = api.session.get_bars(
			symbol = asset.symbol,
			timeframe = timeframe,
			limit = klines,
			start = start_time
		).df
	except Exception as e:
		print("Could Not Get Prices")
		asset.klines = None

    # Manage API calls
	time.sleep(2.1)

    # Return output
	return asset, asset.klines


def get_ticker_position(asset):
	try:
		position_size = api.session.get_position(asset.symbol)
		asset.qty = int(position_size.qty)
	except Exception as e:
		asset.qty = 0
	return asset

def get_orders(position):
	position.has_orders = False
	try:
		orders = api.session.list_orders(status='open', limit=100, nested=True)
		for order in orders:
			if order.symbol == position.symbol:
				position.has_orders = True
				return position
			else:
				position.has_orders = False
		return position
	except Exception as e:
		lg.info("Unable to find orders! %s" % e)
		position.has_orders = False
		return position

def get_tradeable_symbols():

    # Get available symbols
	test_set = slice(0, api.test_set, 1)
	active_assets = api.session.list_assets(status='active')
	asset_list.symbols = [a for a in active_assets if a.easy_to_borrow == True and a.tradable == True and getattr(a, 'class') == 'us_equity']
	asset_list.symbols = asset_list.symbols[test_set]
	Parallel(n_jobs=8, verbose=10, prefer="threads")(delayed(filter_assets)(a) for a in asset_list.symbols)
	asset_list.symbols = [a for a in asset_list.symbols if a.average_volume > 1000000]
	print(len(asset_list.symbols))
	

    # Return ouput
	return asset_list

def filter_assets(a):
	try:
		#a.info = yf.Ticker(a.symbol).info
		#a.average_volume = int(a.info['averageDailyVolume10Day'])
		_, a.day_klines = get_price_klines(a, TimeFrame.Day, 1)
		a.average_volume = int(a.day_klines['volume'][0])
	except Exception as e:
		a.average_volume = 0
	#print(a.symbol, a.average_volume)
	return a

class Orderbook():
	pass


# Place limit or market order
def place_order(asset):

	try:
		asset.order = api.session.submit_order(symbol=asset.symbol, side=asset.side, type="market", qty=asset.quantity, time_in_force='day', stop_loss=dict(stop_price=asset.stop_loss, limit_price=asset.stop_loss))
	except Exception as e:
		lg.info(e)

    # Return order
	return asset
    


# Initialise execution
def initialize_order_execution(asset):
	if hasattr(asset, 'quantity'):
		if asset.quantity > 0:
			order = place_order(asset)
		else:
			lg.info("Quantity is set to zero!")
	else:
		lg.info("Quantity has not been calculated!")
	return asset


#  Place market close order
def place_market_close_order(asset):

    # Close position
	api.session.submit_order(
		symbol=asset.symbol,
		side=asset.side,
		type='market',
		qty=asset.qty,
		time_in_force="gtc"
	)

    # Return
	return
