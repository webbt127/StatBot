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
	lg.info(coint_pairs)
	if not coint_pairs.empty:
		cancel_orders()
		message = 'Starting Trading Bot Interface...'
		send_telegram_message(message, api.telegram_chat_id, api.telegram_api_key)
		if api.use_trade_history:
			open_position_list.positions = pd.read_csv(api.trade_path)
		gui_loop()
