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

global open_position_list

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
			print(open_position_list)
				
				
def sell_loop():
	while True:
		for trade in open_position_list:
			position_1 = position()
			position_1.symbol = open_position_list['sym_1'][trade]
			position_2 = position()
			position_2.symbol = open_position_list['sym_2'][trade]
			get_ticker_position(position_1)
			get_ticker_position(position_2)
		continue

"""STRATEGY CODE"""
if __name__ == "__main__":
    

    # # STEP 1 - Get list of symbols
	lg.info("Getting symbols...")
	test_set = slice(0, 200, 1)
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
