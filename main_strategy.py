import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from helper_functions import *
from config_strategy_api import *
import pandas as pd
from logger import *
import time
import sys
from threading import Thread, Lock
from func_cointegration import *

initialize_logger()

class position_list:
	def __init__(self):
		self.lock = Lock()
		self.positions = pd.DataFrame(columns=['index'])

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
    			
			get_orders(position_1)
			get_orders(position_2)
			get_ticker_position(position_1)
			get_ticker_position(position_2)
			
			trade_complete = False
	
			if position_1.qty == 0 and position_2.qty == 0 and position_1.has_orders == False and position_2.has_orders == False:
				trade_complete = manage_new_trades(position_1, position_2)
			if trade_complete:
				added_to_list = False
				while not added_to_list:
					open_position_list.lock.acquire()
					open_position_list.positions.append(coint_pairs.loc[[i]]
					lg.info(open_position_list.positions)
					added_to_list = True
					open_position_list.lock.release()
				
				
def sell_loop():
	while True:
		#wait_for_market_open()
		open_position_list.lock.acquire()
		open_position_list_working = open_position_list.positions
		open_position_list.lock.release()
		time.sleep(10)
		for trade in open_position_list_working['index']:
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
							removed_from_list = False
							while not removed_from_list:
								open_position_list.lock.acquire()
								open_position_list.remove(trade)
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
						

"""STRATEGY CODE"""
if __name__ == "__main__":
    
	lg.info("Getting symbols...")
	buy_set = slice(0, 10, 1)
	get_tradeable_symbols()
	lg.info("Getting price history...")
	get_price_history()
	lg.info("Calculating co-integration...")
	coint_pairs = get_cointegrated_pairs()
	print(coint_pairs)
	if not coint_pairs.empty:
		cancel_orders()
		begin_threading()
