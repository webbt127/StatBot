import time
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import pandas as pd
import math
import numpy as np
import threading
import yfinance as yf
from threading import Thread, Lock
from config_strategy_api import *
from func_cointegration import *
from telegram_notifications import *
from alive_progress import alive_bar
import logging as lg
from joblib import Parallel, delayed, parallel_backend
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
import datetime
import PySimpleGUI as sg

def exit_handler():
	message = 'Exception Occurred'
	send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
	return

class position_list:
	def __init__(self):
		self.lock = Lock()
		self.positions = pd.DataFrame(columns=['sym_1', 'sym_2', 'p_value', 't_value', 'c_value', 'hedge_ratio', 'zero_crossings', 'sim_profit'])
		
def cancel_orders():
	try:
		api.session.cancel_all_orders()
	except Exception as e:
		lg.info("Unable To Cancel All Orders")

def no_operation():
	return

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

def price_history_execution(asset, minutes=60, klines=api.backtest_bars, use_removal=True, timedelay=True):
	asset.klines = None
	if minutes < 60:
		timeframe = TimeFrame(minutes, TimeFrameUnit.Minute)
	else:
		timeframe = TimeFrame(round(minutes/60), TimeFrameUnit.Hour)
	get_price_klines(asset, timeframe, klines, timedelay)
	#if asset.klines is not None:
		#lg.info("Successfully Stored Data For %s!" % asset.symbol)
	if asset.klines is None and use_removal:
		asset_list.symbols.remove(asset)
		lg.info("Unable To Store Data For %s! Removed From Asset List" % asset.symbol)
	return asset, asset_list

def get_start_time(api):
	time_start_date = 0
	if api.timeframe > 60:
		time_start_date = datetime.datetime.now() - datetime.timedelta(hours=(round(api.timeframe / (api.backtest_bars * (24/7.5)))))
	if api.timeframe == 60:
		time_start_date = datetime.datetime.now() - datetime.timedelta(hours=(api.backtest_bars * (24/7.5)))
	if api.timeframe < 60:
		time_start_date = datetime.datetime.now() - datetime.timedelta(minutes=(api.backtest_bars * api.timeframe * (24/7.5)))
	time_start = time_start_date.isoformat("T") + "Z"
	return time_start

# Get historical prices (klines)
def get_price_klines(asset, timeframe, klines, timedelay=True):

	asset.klines = None
	start_time = get_start_time(api)
	try:
		asset.klines = api.session.get_bars(
			symbol = asset.symbol,
			timeframe = timeframe,
			limit = api.kline_limit,
			start = start_time
		).df
		#print(asset.klines)
	except Exception as e:
		print("Could Not Get Prices")
		asset.klines = None

    # Manage API calls
	if timedelay:
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
	asset_list.symbols = [a for a in asset_list.symbols if a.average_volume > api.min_vol]
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

def add_asset(coint_pairs, open_position_list, i, position_1):
	added_to_list = False
	loc = coint_pairs.loc[coint_pairs.index == i]
	entry = coint_pairs.iloc[loc.index]
	#open_position_list.positions.drop(columns=['Unnamed: 0','index'])
	#entry.drop(columns=['Unnamed: 0'])
	#lg.info("Open Position List: %s" % open_position_list.positions)
	#lg.info(entry)
	while not added_to_list:
		open_position_list.positions = pd.concat([entry, open_position_list.positions])
		if i in open_position_list.positions.index:
			open_position_list.positions.to_csv(api.trade_path, index=False)
			added_to_list = True
	#lg.info(open_position_list.positions)
	return open_position_list
	

def remove_asset(open_position_list, trade):
	removed_from_list = False
	while not removed_from_list:
		open_position_list.lock.acquire()
		open_position_list.positions.drop(trade, inplace=True)
		if trade not in open_position_list.positions.index:
			open_position_list.positions.to_csv(api.trade_path, index=False)
			removed_from_list = True
		#lg.info(trade)
		#lg.info(open_position_list.positions)
		open_position_list.lock.release()
	return open_position_list

def print_close(position_1, position_2, bollinger_up, bollinger_down, spread):
	
	lg.info("========== CHECKING TO CLOSE POSITIONS ==========")
	lg.info("Asset 1: %s" % position_1.symbol)
	lg.info("Asset 2: %s" % position_2.symbol)
	lg.info("BB Upper: %s" % bollinger_up['spread'].iloc[-1])
	lg.info("Spread: %s" % spread)
	lg.info("BB Lower: %s" % bollinger_down['spread'].iloc[-1])
	lg.info("=================================================")
	return
	
def print_open(position_1, position_2, bollinger_up, bollinger_down, spread):
	
	lg.info("========== CHECKING TO OPEN POSITIONS ==========")
	lg.info("Asset 1: %s" % position_1.symbol)
	lg.info("Asset 2: %s" % position_2.symbol)
	lg.info("BB Upper: %s" % bollinger_up['spread'].iloc[-1])
	lg.info("Spread: %s" % spread)
	lg.info("BB Lower: %s" % bollinger_down['spread'].iloc[-1])
	lg.info("=================================================")
	return

def set_order_sides(spread, bollinger_up, bollinger_down, position_1, position_2):
	if spread > bollinger_up['spread'].iloc[-1] or spread < bollinger_down['spread'].iloc[-1]:
		if spread > bollinger_up['spread'].iloc[-1]:
			position_2.side = "sell"
			position_1.side = "buy"
		else:
			position_2.side = "buy"
			position_1.side = "sell"
	return position_1, position_2

def get_yf_info(position):
	try:
		position.yf = yf.Ticker(position.symbol).info
		position.close_series.append(position.yf['regularMarketPrice'])
		if position.yf['regularMarketPrice'] > 0:
			position.quantity = round(api.capital_per_trade / position.yf['regularMarketPrice'])
		else:
			position.quantity = 0
	except:
		position.quantity = 0
	return position

def close_positions(position_1, position_2, open_position_list, trade):
	place_market_close_order(position_1)
	place_market_close_order(position_2)
	message = 'Positions closed for: ' + position_1.symbol + ', ' + position_2.symbol
	send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
	remove_asset(open_position_list, trade)
	return position_1, position_2, open_position_list

def gui(coint_pairs):

	sg.set_options(auto_size_buttons=True)
	#pairs_filename = api.pairs_path
	pairs_filename = "~/cointegrated_pairs.csv"
	#positions_filename = api.trade_path
	positions_filename = "~/trade_history.csv"
    # --- populate table with file contents --- #

	pairs_data = []
	pairs_header_list = []
	positions_data = []
	positions_header_list = []
	series1 = []
	series2 = []
	spread_np = []
	bollinger_up = []
	bollinger_down = []
	position_1 = position()
	position_2 = position()
	positions_df = pd.DataFrame
	GRAPH_SIZE = (500, 500)
	DATA_SIZE = (api.backtest_bars, 30)
	graph = sg.Graph(GRAPH_SIZE, (0, -30), DATA_SIZE, background_color='white', )

	if pairs_filename is not None:
		try:
            # Header=None means you directly pass the columns names to the dataframe
			pairs_df = pd.read_csv(pairs_filename, sep=',', engine='python')
			search_size = slice(0, api.max_search, 1)
			pairs_df = pairs_df[search_size]
			pairs_data = pairs_df.values.tolist()               # read everything else into a list of rows
			pairs_header_list = ['sym_1', 'sym_2', 'p_value', 't_value', 'c_value', 'hedge_ratio', 'zero_crossings', 'sim_profit']
		except:
			sg.popup_error('Error reading file')
			return

	if positions_filename is not None:
		try:
            # Header=None means you directly pass the columns names to the dataframe
			positions_df = pd.read_csv(positions_filename, sep=',', engine='python')
			positions_data = positions_df.values.tolist()               # read everything else into a list of rows
			positions_header_list = ['sym_1', 'sym_2', 'p_value', 't_value', 'c_value', 'hedge_ratio', 'zero_crossings', 'sim_profit']
		except:
			#sg.popup_error('Error reading file')
			lg.info("Error reading positions file")
			#return

	main_layout = [
		[graph,
		sg.Table(values=pairs_data, headings=pairs_header_list, display_row_numbers=True, auto_size_columns=False, num_rows=10, key='-PAIRDATA-', enable_click_events=True)],
		[sg.Table(values=positions_data, headings=positions_header_list, display_row_numbers=True, auto_size_columns=False, num_rows=10, key='-POSITIONDATA-', enable_click_events=True), sg.Multiline(key='-LOG-', size=(60,15), font='Courier 8', expand_x=True, expand_y=True, write_only=True,
                                    reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True)],
			]
	settings_layout = [[sg.Text('Timeframe'), sg.Input(key='-TIMEFRAME-')], [sg.Text('Period Length: '), sg.Input(key='-PERIODINPUT-'), sg.Text('Min Spread: '), sg.Input(key='-MINSPREAD-'), sg.Button('Update')], [sg.Text('STDs'), sg.Input(key='-STD-')], [sg.Text('Backtest Length'), sg.Input(key='-BARS-')]]
	layout = [[sg.TabGroup([[sg.Tab('Main', main_layout), sg.Tab('Settings', settings_layout)]])], [sg.Button('Live Trading'), sg.Button('Backtest'), sg.Button('Exit')]]

	window = sg.Window("Todd's Statistical Arbitrage Bot", layout, grab_anywhere=False)
	while True:
		event, values = window.read(timeout=100)
		graph.Erase()
		if len(spread_np) > 0:
			max_bb = max(spread_np)
			DATA_SIZE = (len(spread_np), max_bb)
		for point in range(len(spread_np)):
			if point > api.bollinger_length:
				graph.DrawLine((point-1, spread_np[point-1]),
					       (point, spread_np[point]), color='blue', width=2)
		for point in range(len(spread_np)):
			if point > api.bollinger_length:
				graph.DrawLine((point-1, bollinger_up['spread'].iloc[point-1]),
					       (point, bollinger_up['spread'].iloc[point]), color='red', width=1)
		for point in range(len(spread_np)):
			if point > api.bollinger_length:
				graph.DrawLine((point-1, bollinger_down['spread'].iloc[point-1]),
					       (point, bollinger_down['spread'].iloc[point]), color='green', width=1)
		for point in range(api.backtest_bars):
			if point > api.bollinger_length:
				graph.DrawLine((point-1, 0),
					       (point, 0), color='red', width=1)
		try:
			positions_df = pd.read_csv(positions_filename, sep=',', engine='python')
			positions_data = positions_df.values.tolist()  # read everything else into a list of rows
			
		except Exception as e:
			lg.info(e)
			
		if event == '__TIMEOUT__' and not positions_df.empty:
			window['-POSITIONDATA-'].update(values=positions_data)#, num_rows=len(positions_df.index))
		if event == 'Update':
			api.bollinger_length = int(values['-PERIODINPUT-'])
			api.min_spread = float(values['-MINSPREAD-'])
			api.std = float(values['-STD-'])
			api.timeframe = int(values['-TIMEFRAME-'])
			api.backtest_bars = int(values['-BARS-'])
		if event == 'Live Trading':
			begin_threading()
		if event == sg.WIN_CLOSED or event == 'Exit':
			break
		if event == 'Backtest':
			run_backtester(coint_pairs)
		if event[0] == '-PAIRDATA-' or event[0] == '-POSITIONDATA-':
			#print("This is an event")
			selected_row = event[2][0]
			hedge_ratio = pairs_df['hedge_ratio'][selected_row]
			if event[0] == '-PAIRDATA-':
				position_1.symbol = pairs_df['sym_1'][selected_row]
				position_2.symbol = pairs_df['sym_2'][selected_row]
				hedge_ratio = pairs_df['hedge_ratio'][selected_row]
			else:
				position_1.symbol = positions_df['sym_1'][selected_row]
				position_2.symbol = positions_df['sym_2'][selected_row]
				hedge_ratio = positions_df['hedge_ratio'][selected_row]
			price_history_execution(position_1, api.timeframe, api.backtest_bars, False)
			price_history_execution(position_2, api.timeframe, api.backtest_bars, False)
			position_1.close_series = extract_close_prices(position_1)
			position_2.close_series = extract_close_prices(position_2)
			#get_yf_info(position_1)
			#get_yf_info(position_2)
			position_1.close_series_matched, position_2.close_series_matched = match_series_lengths(position_1,position_2)
			spread_df, spread_np = calculate_spread(position_1.close_series_matched, position_2.close_series_matched, hedge_ratio)
			if len(spread_np) > 0:
				sma = spread_df.rolling(api.bollinger_length).mean()
				std = spread_df.rolling(api.bollinger_length).std()
				bollinger_up = sma + std * api.std # Calculate top band
				bollinger_down = sma - std * api.std # Calculate bottom band
			else:
				lg.info("Unable to compare pair!")
            
	window.close()

def run_backtester(coint_pairs):
	profit_percent = 0
	position_1 = position()
	position_2 = position()
	coint_pairs['sim_profit'] = None
	search_size = slice(0, api.max_search, 1)
	trade_counter = 0
	win_counter = 0
	for pair in coint_pairs.index[search_size]:
		buy_price1 = None
		buy_price2 = None
		position_1.symbol = coint_pairs['sym_1'][pair]
		position_2.symbol = coint_pairs['sym_2'][pair]
		hedge_ratio = coint_pairs['hedge_ratio'][pair]
		price_history_execution(position_1, api.timeframe, api.backtest_bars, False, False)
		price_history_execution(position_2, api.timeframe, api.backtest_bars, False, False)
		position_1.close_series = extract_close_prices(position_1)
		position_2.close_series = extract_close_prices(position_2)
		position_1.close_series_matched, position_2.close_series_matched = match_series_lengths(position_1,position_2)
		spread_df, spread_np = calculate_spread(position_1.close_series_matched, position_2.close_series_matched, hedge_ratio)
		if len(spread_np) > 0:
			sma = spread_df.rolling(api.bollinger_length).mean()
			std = spread_df.rolling(api.bollinger_length).std()
			bollinger_up = sma + std * api.std # Calculate top band
			bollinger_down = sma - std * api.std # Calculate bottom band
		else:
			lg.info("Unable to compare pair!")
		pair_profit = 0
		for timeslice in spread_df.index-1:
			if spread_df['spread'].iloc[timeslice] > bollinger_up['spread'].iloc[timeslice] and bollinger_up['spread'].iloc[timeslice] > 0 and bollinger_down['spread'].iloc[timeslice] < 0 and buy_price1 == None and abs(spread_df['spread'].iloc[timeslice]) > api.min_spread:
				position_1.side = 'buy'
				position_2.side = 'sell'
				buy_price1 = position_1.close_series[timeslice+1]
				buy_price2 = position_2.close_series[timeslice+1]
				if not api.hide_simulated_trades:
					print('-----SIMULATION OPEN POSITION-----')
					print('Buying ' + position_1.symbol + ' @' + str(buy_price1))
					print('Short selling ' + position_2.symbol + ' @' + str(buy_price2))
					print('Bollinger Up: ' + str(bollinger_up['spread'].iloc[timeslice]))
					print('Spread: ' + str(spread_df['spread'].iloc[timeslice]))
					print('Bollinger Down: ' + str(bollinger_down['spread'].iloc[timeslice]))
					print('----------------------------------')
				trade_counter = trade_counter + 1
			if spread_df['spread'].iloc[timeslice] < bollinger_down['spread'].iloc[timeslice] and bollinger_up['spread'].iloc[timeslice] > 0 and bollinger_down['spread'].iloc[timeslice] < 0 and buy_price1 == None and abs(spread_df['spread'].iloc[timeslice]) > api.min_spread:
				position_1.side = 'sell'
				position_2.side = 'buy'
				buy_price1 = position_1.close_series[timeslice+1]
				buy_price2 = position_2.close_series[timeslice+1]
				if not api.hide_simulated_trades:
					print('-----SIMULATION OPEN POSITION-----')
					print('Buying ' + position_2.symbol + ' @' + str(buy_price2))
					print('Short selling ' + position_1.symbol + ' @' + str(buy_price1))
					print('Bollinger Up: ' + str(bollinger_up['spread'].iloc[timeslice]))
					print('Spread: ' + str(spread_df['spread'].iloc[timeslice]))
					print('Bollinger Down: ' + str(bollinger_down['spread'].iloc[timeslice]))
					print('----------------------------------')
				trade_counter = trade_counter + 1
			if (position_1.side == 'sell' and buy_price1 is not None and spread_df['spread'].iloc[timeslice] > 0) or (buy_price1 is not None and timeslice == (len(spread_df.index) - 1)):
				profit1 = ((float(buy_price1) / float(position_1.close_series[timeslice+1])) - 1.0)
				profit2 = ((float(position_2.close_series[timeslice+1]) / float(buy_price2)) - 1.0)
				pair_profit = pair_profit + profit1 + profit2
				if not api.hide_simulated_trades:
					print('-----SIMULATION CLOSE POSITION-----')
					print('Buying ' + position_1.symbol + ' @' + str(position_1.close_series[timeslice]) + ' (Profit: ' + str(profit1) + ')')
					print('Selling ' + position_2.symbol + ' @' + str(position_2.close_series[timeslice]) + ' (Profit: ' + str(profit2) + ')')
					print('Spread: ' + str(spread_df['spread'].iloc[timeslice])) 
					print('-----------------------------------')
				if (profit1 + profit2) > 0.0:
					win_counter = win_counter + 1
				buy_price1 = None
				buy_price2 = None
			if (position_1.side == 'buy' and buy_price1 is not None and spread_df['spread'].iloc[timeslice] < 0) or (buy_price1 is not None and timeslice == (len(spread_df.index) - 1)):
				profit2 = ((float(buy_price2) / float(position_2.close_series[timeslice+1])) - 1.0)
				profit1 = ((float(position_1.close_series[timeslice+1]) / float(buy_price1)) - 1.0)
				pair_profit = pair_profit + profit1 + profit2
				if not api.hide_simulated_trades:
					print('-----SIMULATION CLOSE POSITION-----')
					print('Buying ' + position_2.symbol + ' @' + str(position_2.close_series[timeslice]) + ' (Profit: ' + str(profit2) + ')')
					print('Selling ' + position_1.symbol + ' @' + str(position_1.close_series[timeslice]) + ' (Profit: ' + str(profit1) + ')')
					print('Spread: ' + str(spread_df['spread'].iloc[timeslice]))
					print('-----------------------------------')
				if (profit1 + profit2) > 0.0:
					win_counter = win_counter + 1
				buy_price1 = None
				buy_price2 = None
		profit_percent = profit_percent + pair_profit
		coint_pairs.loc[pair, 'sim_profit'] = pair_profit
		print('Profit percent for ' + position_1.symbol + '/' + position_2.symbol + ': ' + str(pair_profit))
		if pair_profit < 0.0 and api.sim_break_at_loss:
			break
		pair_profit = 0
		print('Total profit percent: ' + str(profit_percent))
	print('-----RESULTS-----')
	print('Total profit percent: ' + str(profit_percent * 100))
	win_percent = win_counter / trade_counter
	coint_pairs.to_csv(api.pairs_path, index=False)
	print('Win percentage: ' + str(win_percent))
	print('-----------------')

def begin_threading():
	thread1 = Thread(target=buy_loop)
	thread2 = Thread(target=sell_loop)
	thread3 = Thread(target=gui_loop)
	thread1.start()
	time.sleep(5)
	thread2.start()
	time.sleep(5)
	thread3.start()
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
	time.sleep(5)
	try:
		thread3.join()
	except Exception as e:
		lg.info("Exception Handled in Main, Details of the Exception: %s" % e)
		message = 'Exception Occurred: ' + e
		send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)

def gui_loop(coint_pairs):
	gui(coint_pairs)
		
def buy_loop():
	while api.buy:
		wait_for_market_open()
		search_size = slice(0, api.max_search, 1)
		Parallel(n_jobs=6, verbose=10, prefer="threads")(delayed(buy_loop_threaded)(i) for i in coint_pairs.index[search_size])
							
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
			get_price_klines(position_1, TimeFrame.Hour, api.backtest_bars)
			get_price_klines(position_2, TimeFrame.Hour, api.backtest_bars)
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
				#add_asset(coint_pairs, open_position_list, i, position_1)
				if (spread > bollinger_up['spread'].iloc[-1] or spread < bollinger_down['spread'].iloc[-1]) and bollinger_up['spread'].iloc[-1] > 0 and bollinger_down['spread'].iloc[-1] < 0 and coint_pairs['sim_profit'][i] > 0:
					open_position_list.lock.acquire()
					if i not in open_position_list.positions.index:
						initialize_order_execution(position_1)
						initialize_order_execution(position_2)
						message = 'Positions opened for: ' + position_1.symbol + ', ' + position_2.symbol
						send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
						add_asset(coint_pairs, open_position_list, i, position_1)
					open_position_list.lock.release()
				
				
def sell_loop():
	while api.sell:
		wait_for_market_open()
		open_position_list.lock.acquire()
		open_position_list_working = open_position_list
		open_position_list.lock.release()
		time.sleep(10)
		for trade in open_position_list_working.positions.index:
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
			position_1.close_series_matched, position_2.close_series_matched = match_series_lengths(position_1, position_2)
			spread_df, spread_np = calculate_spread(position_1.close_series_matched, position_2.close_series_matched, open_position_list_working.positions.loc[trade]['hedge_ratio'])
			spread_list = spread_df.astype(float).values
			spread = spread_list[-1]
			sma = spread_df.rolling(api.bollinger_length).mean()
			std = spread_df.rolling(api.bollinger_length).std()
			bollinger_up = sma + std * api.std # Calculate top band
			bollinger_down = sma - std * api.std # Calculate bottom band
			print_close(position_1, position_2, bollinger_up, bollinger_down, spread)
			#close_positions(position_1, position_2, open_position_list, trade)
			if position_1.qty > 0 and position_2.qty < 0:
				position_2.qty = abs(position_2.qty)
				position_1.side = 'sell'
				position_2.side = 'buy'
				if (spread < 0):
					no_operation()
					close_positions(position_1, position_2, open_position_list, trade)
			if position_1.qty < 0 and position_2.qty > 0:
				position_1.qty = abs(position_1.qty)
				position_2.side = 'sell'
				position_1.side = 'buy'
				if (spread > 0):
					no_operation()
					close_positions(position_1, position_2, open_position_list, trade)
			#lg.info("Position List:")
			#lg.info(open_position_list_working.positions)	
