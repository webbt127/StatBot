from config_strategy_api import *
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import pandas as pd
import numpy as np
import math
from alive_progress import alive_bar
from joblib import Parallel, delayed, parallel_backend
#from pbar_parallel import PBarParallel, delayed
from func_cointegration import *
import logging as lg
import threading
from ray.util.multiprocessing import Pool


# Calculate spread
def calculate_spread(series_1, series_2, hedge_ratio):
	spread = pd.Series(series_1) - (pd.Series(series_2) * hedge_ratio)
	df = pd.DataFrame()
	df['spread'] = spread
	return df, spread


# Calculate co-integration
def calculate_cointegration(sym_1, sym_2, matched_series_1, matched_series_2):
	coint_flag = 0
	coint_res = coint(matched_series_1, matched_series_2)
	coint_t = coint_res[0]
	p_value = coint_res[1]
	critical_value = coint_res[2][1]
	model = sm.OLS(matched_series_1, matched_series_2).fit()
	hedge_ratio = model.params[0]
	spread, spreadnp = calculate_spread(matched_series_1, matched_series_2, hedge_ratio)
	zero_crossings = len(np.where(np.diff(np.sign(spreadnp)))[0])
	if p_value < 0.05 and coint_t < critical_value:
		coint_flag = 1
	return (coint_flag, round(p_value, 3), round(coint_t, 3), round(critical_value, 3), round(hedge_ratio, 2), zero_crossings)


# Put close prices into a list
def extract_close_prices(asset):
	close_prices = []
	try:
		for price_values in asset.klines['close']:
			close_prices.append(price_values)
	except Exception as e:
		lg.info(e)
	return close_prices


# Calculate cointegrated pairs
def get_cointegrated_pairs():

    # Loop through coins and check for co-integration
	#with alive_bar((len(asset_list.symbols)*len(asset_list.symbols)), title='Checking Cointegration...') as bar:
	global included_list
	Parallel(n_jobs=-1, backend='multiprocessing', verbose=10, prefer="threads")(delayed(check_pairs)(sym_1, sym_2) for sym_1 in asset_list.symbols for sym_2 in asset_list.symbols)
	df_coint = pd.DataFrame(coint_pair_list)
	if 'zero_crossings' in df_coint:
		df_coint = df_coint.sort_values("zero_crossings", ascending=False)
		df_coint = df_coint.reset_index(drop=True)
		#df_coint['index'] = df_coint.index
		df_coint.to_csv(api.pairs_path, index=False)
	return df_coint

def check_pairs(sym_1, sym_2):
	if sym_2 != sym_1:
		sorted_characters = sorted(sym_1.symbol + sym_2.symbol)
		unique = "".join(sorted_characters)
		if unique not in included_list:
			if hasattr(sym_1, 'klines') and hasattr(sym_2, 'klines'):
				if sym_1.klines is not None and sym_2.klines is not None and 'close' in sym_1.klines and 'close' in sym_2.klines:
					sym_1.close_series = extract_close_prices(sym_1)
					sym_2.close_series = extract_close_prices(sym_2)
					matched_series_1, matched_series_2 = match_series_lengths(sym_1, sym_2)
					#lg.info(len(sym_1.close_series_matched))
					#lg.info(len(sym_2.close_series_matched))
					if len(matched_series_1) == len(matched_series_2) and len(matched_series_1) > 0:
						coint_flag, p_value, t_value, c_value, hedge_ratio, zero_crossings = calculate_cointegration(sym_1, sym_2, matched_series_1, matched_series_2)
						if coint_flag == 1 and zero_crossings > api.min_zero_crosses:
							included_list.append(unique)
							coint_pair_list.append({
								"sym_1": sym_1.symbol,
								"sym_2": sym_2.symbol,
								"p_value": p_value,
								"t_value": t_value,
								"c_value": c_value,
								"hedge_ratio": hedge_ratio,
								"zero_crossings": zero_crossings
								})
	#return sym_1, sym_2

def match_series_lengths(position_1, position_2):
	
	if len(position_1.close_series) == len(position_2.close_series):
		matched_series_1 = position_1.close_series
		matched_series_2 = position_2.close_series
		return matched_series_1, matched_series_2
	if len(position_1.close_series) > len(position_2.close_series):
		difference = len(position_1.close_series) - len(position_2.close_series)
		matched_series_1 = position_1.close_series[difference:]
		matched_series_2 = position_2.close_series
		return matched_series_1, matched_series_2
	if len(position_2.close_series) > len(position_1.close_series):
		difference = len(position_2.close_series) - len(position_1.close_series)
		matched_series_1 = position_2.close_series[difference:]
		matched_series_2 = position_1.close_series
		return matched_series_1, matched_series_2
	return matched_series_1, matched_series_2
