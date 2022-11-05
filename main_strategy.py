import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from helper_functions import *
from config_strategy_api import *
import pandas as pd
from logger import *
import time
import sys
import threading
from func_cointegration import *

initialize_logger()

class position_list:
	def __init__(self):
    		pass

global open_position_list
open_position_list = Lock()

def begin_threading():
	thread1 = threading.Thread(target=buy_loop)
	thread2 = threading.Thread(target=sell_loop)
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
		trades_taken = 0
		for i in coint_pairs['index']:
			position_1 = position()
			position_1.symbol = coint_pairs['sym_1'][i]
			position_2 = position()
			position_2.symbol = coint_pairs['sym_2'][i]
    			
			get_orders(position_1)
			get_orders(position_2)
			get_ticker_position(position_1)
			get_ticker_position(position_2)
	
			if position_1.qty == 0 and position_2.qty == 0 and position_1.has_orders == False and position_2.has_orders == False:
				trade_complete = manage_new_trades(position_1, position_2)
			if trade_complete:
				open_position_list[trades_taken] = i
				trades_taken = trades_taken + 1
				added_to_list = False
				while not added_to_list:
					try:
						open_position_list.acquire()
						open_position_list.append(i)
						open_position_list.release()
						added_to_list = True
					except Exception as e:
						lg.info("Asset List is currently locked! %s" % e)
						time.sleep(1)
			print(open_position_list)
				
				
def sell_loop():
	while True:
		try:
			open_position_list.acquire()
			open_position_list_working = open_position_list
			open_position_list.release()
			for trade in open_position_list_working:
				position_1 = position()
				position_1.symbol = trade['sym_1']
				position_2 = position()
				position_2.symbol = trade['sym_2']
				get_ticker_position(position_1)
				get_ticker_position(position_2)
				if position_1.qty != 0 and position_2.qty != 0:
					get_orderbook(position_1)
					get_orderbook(position_2)
					get_price_klines(position_1, TimeFrame.Hour, api.kline_limit)
					get_price_klines(position_2, TimeFrame.Hour, api.kline_limit)
					position_1.close_series = extract_close_prices(position_1)
					position_2.close_series = extract_close_prices(position_2)
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
						else:
							position_2.side = 'sell'
							position_1.side = 'buy'
							if zscore < 0:
								place_market_close_order(position_1)
								place_market_close_order(position_2)
					removed_from_list = False
					while not removed_from_list:
						try:
							open_position_list.acquire()
							open_position_list.remove(trade)
							open_position_list.release()
							removed_from_list = True
						except Exception as e:
							lg.info("Traded Asset List is currently locked! %s" % e)
		except Exception as e:
			lg.info("Traded Asset List is currently locked! %s" % e)
			time.sleep(1)
						

"""STRATEGY CODE"""
if __name__ == "__main__":
    

    # # STEP 1 - Get list of symbols
	lg.info("Getting symbols...")
	test_set = slice(0, 6000, 1)
	buy_set = slice(0, 10, 1)
	get_tradeable_symbols()
	# # Reduce to Test Set
	asset_list.symbols = asset_list.symbols[test_set]
    # # STEP 2 - Construct and save price history
	lg.info("Getting price history...")
	#if len(asset_list) > 0:
	get_price_history()

    # # STEP 3 - Find Cointegrated pairs
	lg.info("Calculating co-integration...")
	#if len(asset_list) > 0:
	coint_pairs = get_cointegrated_pairs()
	print(coint_pairs)
        
    # # STEP 4
	cancel_orders()
	begin_threading()
