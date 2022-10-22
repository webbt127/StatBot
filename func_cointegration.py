from config_strategy_api import *
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import pandas as pd
import numpy as np
import math
from alive_progress import alive_bar
from joblib import Parallel, delayed, parallel_backend


# Calculate Z-Score
def calculate_zscore(spread):
	df = pd.DataFrame(spread)
	mean = df.rolling(center=False, window=z_score_window).mean()
	std = df.rolling(center=False, window=z_score_window).std()
	x = df.rolling(center=False, window=1).mean()
	df["ZSCORE"] = (x - mean) / std
	return df["ZSCORE"].astype(float).values


# Calculate spread
def calculate_spread(series_1, series_2, hedge_ratio):
	spread = pd.Series(series_1) - (pd.Series(series_2) * hedge_ratio)
	return spread


# Calculate co-integration
def calculate_cointegration(sym_1, sym_2):
	coint_flag = 0
	coint_res = coint(sym_1.close_series, sym_2.close_series)
	coint_t = coint_res[0]
	p_value = coint_res[1]
	critical_value = coint_res[2][1]
	model = sm.OLS(sym_1.close_series, sym_2.close_series).fit()
	hedge_ratio = model.params[0]
	spread = calculate_spread(sym_1.close_series, sym_2.close_series, hedge_ratio)
	zero_crossings = len(np.where(np.diff(np.sign(spread)))[0])
	if p_value < 0.5 and coint_t < critical_value:
		coint_flag = 1
	return (coint_flag, round(p_value, 3), round(coint_t, 3), round(critical_value, 3), round(hedge_ratio, 2), zero_crossings)


# Put close prices into a list
def extract_close_prices(asset):
	close_prices = []
	for price_values in asset.klines['close']:
		close_prices.append(price_values)
	return close_prices


# Calculate cointegrated pairs
def get_cointegrated_pairs():

    # Loop through coins and check for co-integration
	coint_pair_list = []
	included_list = []
	with alive_bar(0, title='Checking Cointegration...') as bar:
		Parallel(n_jobs=8, prefer="threads")(delayed(check_pairs)(sym_1, sym_2) for sym_1 in asset_list.symbols for sym_2 in asset_list.symbols)
		df_coint = pd.DataFrame(coint_pair_list)
		df_coint = df_coint.sort_values("zero_crossings", ascending=False)
		df_coint = df_coint.reset_index(drop=True)
		df_coint.to_csv("2_cointegrated_pairs.csv")
		return df_coint
	
def check_pairs(sym_1, sym_2):
	if sym_2 != sym_1:
		sorted_characters = sorted(sym_1.symbol + sym_2.symbol)
		unique = "".join(sorted_characters)
		if unique not in included_list:
			if sym_1.klines is not None and sym_2.klines is not None and 'close' in sym_1.klines and 'close' in sym_2.klines:
				sym_1.close_series = extract_close_prices(sym_1)
				sym_2.close_series = extract_close_prices(sym_2)
				if len(sym_1.close_series) == len(sym_2.close_series):
					coint_flag, p_value, t_value, c_value, hedge_ratio, zero_crossings = calculate_cointegration(sym_1, sym_2)
					if coint_flag == 1:
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
