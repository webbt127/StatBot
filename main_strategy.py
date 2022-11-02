import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from helper_functions import *
from config_strategy_api import *
import pandas as pd
from logger import *
import time
import sys
from func_cointegration import *

initialize_logger()

"""STRATEGY CODE"""
if __name__ == "__main__":
    

    # # STEP 1 - Get list of symbols
	lg.info("Getting symbols...")
	test_set = slice(0, 200, 1)
	buy_set = slice(0, 10, 1)
	get_tradeable_symbols()
	# # Test Set
	asset_list.symbols = asset_list.symbols[test_set]
    # # STEP 2 - Construct and save price history
	lg.info("Constructing and saving price data to JSON...")
	#if len(asset_list) > 0:
	get_price_history()

    # # STEP 3 - Find Cointegrated pairs
	lg.info("Calculating co-integration...")
	#if len(asset_list) > 0:
	coint_pairs = get_cointegrated_pairs()
	print(coint_pairs)
        
    # # STEP 4
	begin_threading(buy_loop, sell_loop)
	
def buy_loop():
	while True:
		wait_for_market_open()
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
				manage_new_trades(position_1, position_2)
			else:
				continue
				
def sell_loop():
	while True:
		continue
