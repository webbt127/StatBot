import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from func_get_symbols import *
from func_prices_json import *
from func_cointegration import *
from config_strategy_api import *
#from func_plot_trends import plot_trends
import pandas as pd
import json
from json import JSONEncoder
import pickle
import shelve
import persistent
from logger import *
from func_position_calls import *
from func_trade_management import *
from func_execution_calls import *
from func_close_positions import *
import time
import sys
from func_execution_calls import *

initialize_logger()

"""STRATEGY CODE"""
if __name__ == "__main__":
    

    # # STEP 1 - Get list of symbols
	lg.info("Getting symbols...")
	get_tradeable_symbols()

    # # STEP 2 - Construct and save price history
	lg.info("Constructing and saving price data to JSON...")
	if len(asset_list.symbols) > 0 and api.get_new_history:
		get_price_history()
		filehandler = open('data.pickle', 'wb') 
		pickle.dump(asset_list, filehandler)
	else:
		filehandler = open('data.pickle', 'rb') 
		asset_list = pickle.load(filehandler)

    # # STEP 3 - Find Cointegrated pairs
	lg.info("Calculating co-integration...")
	if len(asset_list.symbols) > 0:
		coint_pairs = get_cointegrated_pairs()
		print(coint_pairs)
        
    # # STEP 4
	while 1:
		for i in coint_pairs['sym_1']:
			if int(i) < api.max_positions:
				position_1 = position()
				position_1.symbol = coint_pairs['sym_1'][i]
				position_2 = position()
				position_2.symbol = coint_pairs['sym_2'][i]
    
				get_ticker_position(position_1)
				get_ticker_position(position_2)
	
				if position_1.qty != 0 and position_2.qty != 0:
					is_manage_new_trades = True
				else:
					is_manage_new_trades = False
		
				if is_manage_new_trades:
					signal_side = manage_new_trades(position_1, position_2)
