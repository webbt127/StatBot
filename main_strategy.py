import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from helper_functions import *
from config_strategy_api import *
import pandas as pd
from logger import *
import time
import sys
import yfinance as yf
from threading import Thread, Lock
from func_cointegration import *

initialize_logger()

class position_list:
	def __init__(self):
		self.lock = Lock()
		self.positions = pd.DataFrame(columns=['sym_1', 'sym_2', 'p_value', 't_value', 'c_value', 'hedge_ratio', 'zero_crossings', 'index'])

global open_position_list
open_position_list = position_list()

def begin_threading():
	thread1 = Thread(target=buy_loop)
	thread2 = Thread(target=sell_loop)
	thread1.start()
	time.sleep(5)
	thread2.start()
	time.sleep(5)
	try:
		thread1.join()
	except Exception as e:
        	lg.info("Exception Handled in Main, Details of the Exception: %s" % e)
	time.sleep(5)
	try:
		thread2.join()
	except Exception as e:
        	lg.info("Exception Handled in Main, Details of the Exception: %s" % e)

	
def buy_loop():
	while True:
		#wait_for_market_open()
		for i in coint_pairs['index']:
			position_1 = position()
			position_1.symbol = coint_pairs['sym_1'][i]
			position_2 = position()
			position_2.symbol = coint_pairs['sym_2'][i]
			
			open_position_list.lock.acquire()
			open_position_list_temp = open_position_list
			open_position_list.lock.release()
			
			if position_1.symbol not in open_position_list_temp.positions['sym_1'] or position_1.symbol not in open_position_list_temp.positions['sym_1']:
				if position_2.symbol not in open_position_list_temp.positions['sym_1'] or position_2.symbol not in open_position_list_temp.positions['sym_1']:
					get_price_klines(position_1, TimeFrame.Hour, api.kline_limit)
					get_price_klines(position_2, TimeFrame.Hour, api.kline_limit)
					position_1.close_series = extract_close_prices(position_1)
					position_1.yf = yf.Ticker(position_1.symbol).info
					position_1.close_series.append(position_1.yf['regularMarketPrice'])
					position_2.close_series = extract_close_prices(position_2)
					position_2.yf = yf.Ticker(position_2.symbol).info
					position_2.close_series.append(position_2.yf['regularMarketPrice'])
					position_1.quantity = round(api.capital_per_trade / position_1.yf['regularMarketPrice'])
					position_2.quantity = round(api.capital_per_trade / position_2.yf['regularMarketPrice'])
	
					if(len(position_1.close_series) == len(position_2.close_series) and len(position_1.close_series) > 0):
						_, _, _, _, hedge_ratio, _ = calculate_cointegration(position_1, position_2)
						spread = calculate_spread(position_1.close_series, position_2.close_series, hedge_ratio)
						zscore_list = calculate_zscore(spread)
						zscore = zscore_list[-1]
	
						if abs(zscore) > api.signal_trigger_thresh:
							if zscore > 0:
								position_1.side = "sell"
								position_2.side = "buy"
							else:
								position_1.side = "buy"
								position_2.side = "sell"

							initialize_order_execution(position_1)
							initialize_order_execution(position_2)
							added_to_list = False
							while not added_to_list:
								open_position_list.lock.acquire()
								lg.info(coint_pairs.loc[[i]])
								entry = coint_pairs.loc[coint_pairs['index'] == i]
								open_position_list.positions = pd.concat([open_position_list.positions, entry])
								lg.info("Position List:")
								lg.info(open_position_list.positions)
								added_to_list = True
								open_position_list.lock.release()
				
				
def sell_loop():
	while True:
		#wait_for_market_open()
		open_position_list.lock.acquire()
		open_position_list_working = open_position_list
		open_position_list.lock.release()
		time.sleep(10)
		for trade in open_position_list_working.positions['index']:
			position_1 = position()
			position_1.symbol = trade['sym_1']
			position_2 = position()
			position_2.symbol = trade['sym_2']
			get_ticker_position(position_1)
			get_ticker_position(position_2)
			get_price_klines(position_1, TimeFrame.Hour, api.kline_limit)
			get_price_klines(position_2, TimeFrame.Hour, api.kline_limit)
			position_1.close_series = extract_close_prices(position_1)
			position_1.yf = yf.Ticker(position_1.symbol).info
			position_1.close_series.append(position_1.yf['regularMarketPrice'])
			position_2.close_series = extract_close_prices(position_2)
			position_2.yf = yf.Ticker(position_2.symbol).info
			position_2.close_series.append(position_2.yf['regularMarketPrice'])
			if(len(position_1.close_series) == len(position_2.close_series) and len(position_1.close_series) > 0):
				_, _, _, _, hedge_ratio, _ = calculate_cointegration(position_1, position_2)
				spread = calculate_spread(position_1.close_series, position_2.close_series, hedge_ratio)
				zscore_list = calculate_zscore(spread)
				zscore = zscore_list[-1]
				if position_1.qty > 0:
					position_1.side = 'sell'
					position_2.side = 'buy'
					if zscore > 0:
						place_market_close_order(position_1)
						place_market_close_order(position_2)
						removed_from_list = False
						while not removed_from_list:
							open_position_list.lock.acquire()
							open_position_list.positions.remove(trade)
							removed_from_list = True
							open_position_list.lock.release()
				else:
					position_2.side = 'sell'
					position_1.side = 'buy'
					if zscore < 0:
						place_market_close_order(position_1)
						place_market_close_order(position_2)
						removed_from_list = False
						while not removed_from_list:
							open_position_list.lock.acquire()
							open_position_list.remove(trade)
							removed_from_list = True
							open_position_list.lock.release()
				lg.info("Position List:")
				lg.info(open_position_list_working.positions)	

"""STRATEGY CODE"""
if __name__ == "__main__":
    
	lg.info("Getting symbols...")
	buy_set = slice(0, 10, 1)
	get_tradeable_symbols()
	lg.info("Getting price history...")
	get_price_history()
	lg.info("Calculating co-integration...")
	coint_pairs = get_cointegrated_pairs()
	lg.info(coint_pairs)
	if not coint_pairs.empty:
		cancel_orders()
		begin_threading()
