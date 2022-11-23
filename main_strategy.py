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
from telegram_notifications import *
import urllib3
import atexit

initialize_logger()

atexit.register(exit_handler)
global open_position_list
open_position_list = position_list()

urllib3.disable_warnings()

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
		message = 'Exception Occurred: ' + e
		send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
	time.sleep(5)
	try:
		thread2.join()
	except Exception as e:
		lg.info("Exception Handled in Main, Details of the Exception: %s" % e)
		message = 'Exception Occurred: ' + e
		send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)

	
def buy_loop():
	while api.threaded:
		Parallel(n_jobs=6, verbose=10, prefer="threads")(delayed(buy_loop_threaded)(i) for i in coint_pairs['index'])
	while not api.threaded:
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
					get_yf_info(position_1)
					get_yf_info(position_2)
					position_1.close_series_matched, position_2.close_series_matched = match_series_lengths(position_1, position_2)
					if(len(position_1.close_series_matched) == len(position_2.close_series_matched) and len(position_1.close_series_matched) > 0 and position_1.quantity > 0 and position_2.quantity > 0):
						position_1.stop_loss = round(position_1.close_series_matched[-1] * (1 - api.stop_loss_fail_safe), api.price_rounding)
						position_2.stop_loss = round(position_2.close_series_matched[-1] * (1 - api.stop_loss_fail_safe), api.price_rounding)
						spread_df, spread_np = calculate_spread(position_1.close_series_matched, position_2.close_series_matched, coint_pairs['hedge_ratio'][i])
						spread_list = spread_df.astype(float).values
						spread = spread_list[-1]
						sma = spread_df.rolling(api.bollinger_length).mean()
						std = spread_df.rolling(api.bollinger_length).std()
						bollinger_up = sma + std * api.std # Calculate top band
						bollinger_down = sma - std * api.std # Calculate bottom band
						print_open(position_1, position_2, bollinger_up, bollinger_down, spread)
						set_order_sides(spread, bollinger_up, bollinger_down, position_1, position_2)
						add_asset(coint_pairs, open_position_list, i, position_1)
						if spread > bollinger_up['spread'].iloc[-1] or spread < bollinger_down['spread'].iloc[-1]:
							open_position_list.lock.acquire()
							if i not in open_position_list.positions['index']:
								initialize_order_execution(position_1)
								initialize_order_execution(position_2)
								message = 'Positions opened for: ' + position_1.symbol + ', ' + position_2.symbol
								send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
								#add_asset(coint_pairs, open_position_list, i, position_1)
							open_position_list.lock.release()
							
def buy_loop_threaded(i):
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
			get_yf_info(position_1)
			get_yf_info(position_2)
			position_1.close_series_matched, position_2.close_series_matched = match_series_lengths(position_1, position_2)
			if(len(position_1.close_series_matched) == len(position_2.close_series_matched) and len(position_1.close_series_matched) > 0 and position_1.quantity > 0 and position_2.quantity > 0):
				position_1.stop_loss = round(position_1.close_series_matched[-1] * (1 - api.stop_loss_fail_safe), api.price_rounding)
				position_2.stop_loss = round(position_2.close_series_matched[-1] * (1 - api.stop_loss_fail_safe), api.price_rounding)
				spread_df, spread_np = calculate_spread(position_1.close_series_matched, position_2.close_series_matched, coint_pairs['hedge_ratio'][i])
				spread_list = spread_df.astype(float).values
				spread = spread_list[-1]
				sma = spread_df.rolling(api.bollinger_length).mean()
				std = spread_df.rolling(api.bollinger_length).std()
				bollinger_up = sma + std * 2 # Calculate top band
				bollinger_down = sma - std * 2 # Calculate bottom band
				print_open(position_1, position_2, bollinger_up, bollinger_down, spread)
				set_order_sides(spread, bollinger_up, bollinger_down, position_1, position_2)
				add_asset(coint_pairs, open_position_list, i, position_1)
				if spread > bollinger_up['spread'].iloc[-1] or spread < bollinger_down['spread'].iloc[-1]:
					open_position_list.lock.acquire()
					if i not in open_position_list.positions['index']:
						initialize_order_execution(position_1)
						initialize_order_execution(position_2)
						message = 'Positions opened for: ' + position_1.symbol + ', ' + position_2.symbol
						send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
						#add_asset(coint_pairs, open_position_list, i, position_1)
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
			position_2.close_series = extract_close_prices(position_2)
			get_yf_info(position_1)
			get_yf_info(position_2)
			position_1.close_series_matched, position_2.close_series_matched = match_series_lengths(position_1, positions_2)
			spread_df, spread_np = calculate_spread(position_1.close_series_matched, position_2.close_series_matched, open_position_list_working.positions[trade]['hedge_ratio'])
			spread_list = spread_df.astype(float).values
			spread = spread_list[-1]
			sma = spread_df.rolling(api.bollinger_length).mean()
			std = spread_df.rolling(api.bollinger_length).std()
			bollinger_up = sma + std * 2 # Calculate top band
			bollinger_down = sma - std * 2 # Calculate bottom band
			print_close(position_1, position_2, bollinger_up, bollinger_down, spread)
			if position_1.qty > 0 and position_2.qty < 0:
				position_2.qty = abs(position_2.qty)
				position_1.side = 'sell'
				position_2.side = 'buy'
				if spread > 0 or spread > bollinger_up['spread'].iloc[-1]:
					close_positions(position_1, position_2, open_position_list, trade)
			if position_1.qty < 0 and position_2.qty > 0:
				position_1.qty = abs(position_1.qty)
				position_2.side = 'sell'
				position_1.side = 'buy'
				if spread < 0 or spread < bollinger_down['spread'].iloc[-1]:
					close_positions(position_1, position_2, open_position_list, trade)
			lg.info("Position List:")
			lg.info(open_position_list_working.positions)	

"""STRATEGY CODE"""
if __name__ == "__main__":
    
	get_new_pairs = input('Get New Pairs? (y/n)')
	if get_new_pairs == 'y':
		lg.info("Getting symbols...")
		get_tradeable_symbols()
		lg.info("Getting price history...")
		get_price_history()
		lg.info("Calculating co-integration...")
		coint_pairs = get_cointegrated_pairs()
	if get_new_pairs == 'n':
		coint_pairs = pd.read_csv(api.pairs_path)
	coint_pairs.drop(columns='Unnamed: 0')
	lg.info(coint_pairs)
	if not coint_pairs.empty:
		cancel_orders()
		message = 'Starting Trading Bot Interface...'
		send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
		begin_threading()
