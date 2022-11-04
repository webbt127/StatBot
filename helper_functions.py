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
from alpaca_trade_api.rest import TimeFrame
import datetime


# Manage new trade assessment and order placing
def manage_new_trades(position_1, position_2):
    # Get and save the latest z-score
	get_orderbook(position_1)
	get_orderbook(position_2)
	
	get_price_klines(position_1)
	get_price_klines(position_2)
	position_1.close_series = extract_close_prices(position_1)
	position_2.close_series = extract_close_prices(position_2)
	
	if(len(position_1.close_series) == len(position_2.close_series) and len(position_1.close_series) > 0):
		_, _, _, _, hedge_ratio, _ = calculate_cointegration(position_1, position_2)
		spread = calculate_spread(position_1.close_series, position_2.close_series, hedge_ratio)
		zscore_list = calculate_zscore(spread)
		zscore = zscore_list[-1]
	
		if zscore > 0:
			position_1.direction = "Short"
			position_2.direction = "Long"
		else:
			position_1.direction = "Long"
			position_2.direction = "Short"
		
		get_mid_price(position_1)
		get_mid_price(position_2)

    # Switch to hot if meets signal threshold
    # Note: You can add in coint-flag check too if you want extra vigilence
		get_trade_details(position_1, api.tradable_capital_usdt)
		get_trade_details(position_2, api.tradable_capital_usdt)
		if abs(zscore) > api.signal_trigger_thresh:

        # Get trades history for liquidity
			get_ticker_trade_liquidity(position_2)
			get_ticker_trade_liquidity(position_1)

        # Determine long ticker vs short ticker
			if zscore > 0:
				long_ticker = position_2
				short_ticker = position_1
				avg_liquidity_long = position_2.liquidity
				avg_liquidity_short = position_1.liquidity
				last_price_long = position_2.last_price
				last_price_short = position_1.last_price
			else:
				long_ticker = position_1
				short_ticker = position_2
				avg_liquidity_long = position_1.liquidity
				avg_liquidity_short = position_2.liquidity
				last_price_long = position_1.last_price
				last_price_short = position_2.last_price

			initialize_order_execution(long_ticker)
			initialize_order_execution(short_ticker)
			
			time.sleep(10)
			
			get_ticker_position(long_ticker)
			get_ticker_position(short_ticker)
			
			while long_ticker.qty == 0:
				api.session.cancel_order(long_ticker.order.id)
				long_ticker.mid_price = round(long_ticker.mid_price * 1.01, 2)
				initialize_order_execution(long_ticker)
				time.sleep(10)
				get_ticker_position(long_ticker)
			while short_ticker.qty == 0:
				api.session.cancel_order(short_ticker.order.id)
				short_ticker.mid_price = round(short_ticker.mid_price * 0.99, 2)
				initialize_order_execution(short_ticker)
				time.sleep(10)
				get_ticker_position(short_ticker)
			if long_ticker.qty != 0 and short_ticker.qty != 0:
				return True
			else:
				return False
	else:
		lg.info("Klines have unequal length, cannot calculate cointegration!")


    # Output status
	return False

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
	return clock

def get_orderbook(asset):

	asset.orderbook = Orderbook()
	asset.latest_quote = api.session.get_latest_quote(asset.symbol)
	asset.orderbook.ap = getattr(asset.latest_quote, 'ap')
	asset.orderbook.bp = getattr(asset.latest_quote, 'bp')
	return asset

def get_mid_price(asset):
	if asset.direction == "Long":
		asset.mid_price = asset.orderbook.bp # placing at Bid has high probability of not being cancelled, but may not fill
	else:
		asset.mid_price = asset.orderbook.ap  # placing at Ask has high probability of not being cancelled, but may not fill
	return asset


# Get trade details and latest prices
def get_trade_details(asset, capital):

    # Set calculation and output variables
	asset.price_rounding = 20
	asset.quantity_rounding = 20
	asset.mid_price = 0
	asset.quantity = 0
	asset.stop_loss = 0

    # Get prices, stop loss and quantity
	if hasattr(asset, 'orderbook'):

        # Set price rounding
		asset.price_rounding = api.rounding_ticker_1 if asset.symbol == api.ticker_1 else api.rounding_ticker_2
		asset.quantity_rounding = api.quantity_rounding_ticker_1 if asset.symbol == api.ticker_1 else api.quantity_rounding_ticker_2

            # Calculate hard stop loss
	if asset.direction == "Long":
		asset.mid_price = asset.orderbook.bp # placing at Bid has high probability of not being cancelled, but may not fill
		asset.stop_loss = round(asset.mid_price * (1 - api.stop_loss_fail_safe), api.price_rounding)
	else:
		asset.mid_price = asset.orderbook.ap  # placing at Ask has high probability of not being cancelled, but may not fill
		asset.stop_loss = round(asset.mid_price * (1 + api.stop_loss_fail_safe), api.price_rounding)

            # Calculate quantity
	if asset.mid_price > 0:
		asset.quantity = round(capital / asset.mid_price)
	else:
		asset.quantity = 0

    # Output results
	return asset

def get_price_history():

    # Get prices and store in DataFrame
	price_history_dict = {}
	Parallel(n_jobs=8, prefer="threads")(delayed(price_history_execution)(asset) for asset in asset_list.symbols)	
    # Return output
	return asset_list

def price_history_execution(asset):
	asset.klines = None
	get_price_klines(asset)
	if asset.klines is not None:
		lg.info("Successfully Stored Data For %s!" % asset.symbol)
	else:
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
def get_price_klines(asset):

	start_time = get_start_time(api)
	try:
		asset.klines = api.session.get_bars(
			symbol = asset.symbol,
			timeframe = TimeFrame.Hour,
			limit = api.kline_limit,
			start = start_time
		).df
	except Exception as e:
		print("Could Not Get Prices")
		asset.klines = None

    # Manage API calls
	time.sleep(1.7)

    # Return output
	return asset

def get_ticker_trade_liquidity(position):

    # Get trades history
	try:
		trades = api.session.get_trades(symbol=position.symbol, limit=5)
	except:
		lg.info("Unable to get trades %s" % e)

    # Get the list for calculating the average liquidity
	quantity_list = []
	for trade in trades:
		if hasattr(trade, 's'):
			quantity_list.append(trade.s)

    # Return output
	if len(quantity_list) > 0:
		position.liquidity = sum(quantity_list) / len(quantity_list)
		position.last_price = float(trades[-1].p)
		return position
	position.liquidity = 0
	position.last_price = 0
	return position

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
	active_assets = api.session.list_assets(status='active')
	for a in active_assets:
		stock_info = yf.Ticker(a).info
		stock_price = stock_info['regularMarketPrice']
		print(stock_info)
	asset_list.symbols = [a for a in active_assets if a.easy_to_borrow == True and a.tradable == True and getattr(a, 'class') == 'us_equity']
	

    # Return ouput
	return asset_list

class Orderbook():
	pass


# Place limit or market order
def place_order(asset):

    # Set variables
	if asset.direction == "Long":
		asset.side = "buy"
	else:
		asset.side = "sell"

	try:
		asset.order = api.session.submit_order(symbol=asset.symbol, side=asset.side, type="limit", qty=asset.quantity, limit_price=asset.mid_price, time_in_force='day', stop_loss=dict(stop_price=asset.stop_loss, limit_price=asset.stop_loss))
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

def get_position_info(asset):

    # Declare output variables
	asset.side = 0
	asset.size = ""

    # Extract position info
	try:
		asset.position = api.session.get_position(ticker)
		asset.size = int(asset.position.qty)
		if asset.size > 0:
			asset.side = "Buy"
		else:
			asset.side = "Sell"
	except Exception as e:
		#lg.info("No Existing Position For %s!" % asset.symbol)
		asset.size = 0
		asset.side = "Sell"

    # Return output
	return asset


#  Place market close order
def place_market_close_order(asset):

    # Close position
	api.session.submit_order(
		symbol=asset.symbol,
		side=asset.side,
		type='market',
		qty=asset.size,
		time_in_force="gtc"
	)

    # Return
	return
