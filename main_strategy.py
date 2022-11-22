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
		self.positions = pd.DataFrame(columns=['sym_1', 'sym_2', 'p_value', 't_value', 'c_value', 'hedge_ratio', 'zero_crossings', 'index', 'hedge_ratio'])

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
		wait_for_market_open()
		for i in coint_pairs['index']:
			position_1 = position()
			position_1.symbol = coint_pairs['sym_1'][i]
			position_2 = position()
			position_2.symbol = coint_pairs['sym_2'][i]
			
			open_position_list.lock.acquire()
			open_position_list_temp = open_position_list
			open_position_list.lock.release()
			
			if open_position_list_temp.positions['sym_1'].str.contains(position_1.symbol).sum() == 0 and open_position_list_temp.positions['sym_1'].str.contains(position_2.symbol).sum() == 0:
				if open_position_list_temp.positions['sym_2'].str.contains(position_1.symbol).sum() == 0 and open_position_list_temp.positions['sym_2'].str.contains(position_2.symbol).sum() == 0:
					get_price_klines(position_1, TimeFrame.Hour, api.kline_limit)
					get_price_klines(position_2, TimeFrame.Hour, api.kline_limit)
					position_1.close_series = extract_close_prices(position_1)
					position_2.close_series = extract_close_prices(position_2)
					#match_series_lengths(position_1, positions_2)
					try:
						position_1.yf = yf.Ticker(position_1.symbol).info
						position_1.close_series.append(position_1.yf['regularMarketPrice'])
						if position_1.yf['regularMarketPrice'] > 0:
							position_1.quantity = round(api.capital_per_trade / position_1.yf['regularMarketPrice'])
						else:
							position_1.quantity = 0
					except:
						position_1.quantity = 0
					try:
						position_2.yf = yf.Ticker(position_2.symbol).info
						position_2.close_series.append(position_2.yf['regularMarketPrice'])
						if position_2.yf['regularMarketPrice'] > 0:
							position_2.quantity = round(api.capital_per_trade / position_2.yf['regularMarketPrice'])
						else:
							position_2.quantity = 0
					except:
						position_2.quantity = 0
	
					if(len(position_1.close_series) == len(position_2.close_series) and len(position_1.close_series) > 0 and position_1.quantity > 0 and position_2.quantity > 0):
						position_1.stop_loss = round(position_1.close_series[-1] * (1 - api.stop_loss_fail_safe), api.price_rounding)
						position_2.stop_loss = round(position_2.close_series[-1] * (1 - api.stop_loss_fail_safe), api.price_rounding)
						_, _, _, _, hedge_ratio, _ = calculate_cointegration(position_1, position_2)
						spread_df, spread_np = calculate_spread(position_1.close_series, position_2.close_series, hedge_ratio)
						spread_list = spread_df.astype(float).values
						spread = spread_list[-1]
						sma = spread_df.rolling(api.bollinger_length).mean()
						std = spread_df.rolling(api.bollinger_length).std()
						bollinger_up = sma + std * 2 # Calculate top band
						bollinger_down = sma - std * 2 # Calculate bottom band
						lg.info("========== CHECKING TO OPEN POSITIONS ==========")
						lg.info("Asset 1: %s" % position_1.symbol)
						lg.info("Asset 2: %s" % position_2.symbol)
						lg.info("BB Upper: %s" % bollinger_up['spread'].iloc[-1])
						lg.info("Spread: %s" % spread)
						lg.info("BB Lower: %s" % bollinger_down['spread'].iloc[-1])
						lg.info("=================================================")
	
						if spread > bollinger_up['spread'].iloc[-1] or spread < bollinger_down['spread'].iloc[-1]:
							if spread > bollinger_up['spread'].iloc[-1]:
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
								lg.info("Open Position List: %s" % open_position_list.positions)
								entry = coint_pairs.loc[coint_pairs['index'] == i]
								open_position_list.positions = pd.concat([open_position_list.positions, entry])
								added_to_list = True
								open_position_list.lock.release()
				
				
def sell_loop():
	while True:
		wait_for_market_open()
		open_position_list.lock.acquire()
		open_position_list_working = open_position_list
		open_position_list.lock.release()
		time.sleep(10)
		for trade in open_position_list_working.positions['index']:
			position_1 = position()
			position_1.symbol = open_position_list_working.positions.loc[trade]['sym_1']
			position_2 = position()
			position_2.symbol = open_position_list_working.positions.loc[trade]['sym_2']
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
			#match_series_lengths(position_1, positions_2)
			spread_df, spread_np = calculate_spread(position_1.close_series, position_2.close_series, open_position_list_working.positions[trade]['hedge_ratio'])
			spread_list = spread_df.astype(float).values
			spread = spread_list[-1]
			sma = spread_df.rolling(api.bollinger_length).mean()
			std = spread_df.rolling(api.bollinger_length).std()
			bollinger_up = sma + std * 2 # Calculate top band
			bollinger_down = sma - std * 2 # Calculate bottom band
			lg.info("========== CHECKING TO CLOSE POSITIONS ==========")
			lg.info("Asset 1: %s" % position_1.symbol)
			lg.info("Asset 2: %s" % position_2.symbol)
			lg.info("BB Upper: %s" % bollinger_up['spread'].iloc[-1])
			lg.info("Spread: %s" % spread)
			lg.info("BB Lower: %s" % bollinger_down['spread'].iloc[-1])
			lg.info("=================================================")
			if position_1.qty > 0 and position_2.qty < 0:
				position_2.qty = abs(position_2.qty)
				position_1.side = 'sell'
				position_2.side = 'buy'
				if spread > 0 or spread > bollinger_up['spread'].iloc[-1]:
					place_market_close_order(position_1)
					place_market_close_order(position_2)
					removed_from_list = False
					while not removed_from_list:
						open_position_list.lock.acquire()
						open_position_list.positions.drop(trade)
						removed_from_list = True
						open_position_list.lock.release()
			if position_1.qty < 0 and position_2.qty > 0:
				position_1.qty = abs(position_1.qty)
				position_2.side = 'sell'
				position_1.side = 'buy'
				if spread < 0 or spread < bollinger_down['spread'].iloc[-1]:
					place_market_close_order(position_1)
					place_market_close_order(position_2)
					removed_from_list = False
					while not removed_from_list:
						open_position_list.lock.acquire()
						open_position_list.positions.remove(trade)
						removed_from_list = True
						open_position_list.lock.release()
			lg.info("Position List:")
			lg.info(open_position_list_working.positions)	

"""STRATEGY CODE"""
if __name__ == "__main__":
    
	get_new_pairs = input('Get New Pairs? (y/n)'
	if get_new_pairs == 'y':
		lg.info("Getting symbols...")
		buy_set = slice(0, 10, 1)
		get_tradeable_symbols()
		lg.info("Getting price history...")
		get_price_history()
		lg.info("Calculating co-integration...")
		coint_pairs = get_cointegrated_pairs()
	
	if get_new_pairs == 'n':
		coint_pairs = pd.read_csv("2_cointegrated_pairs.csv")
	lg.info(coint_pairs)
	if not coint_pairs.empty:
		cancel_orders()
		begin_threading()
