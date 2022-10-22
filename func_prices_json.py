from func_price_klines import get_price_klines
import json
from alive_progress import alive_bar
import logging as lg
from joblib import Parallel, delayed, parallel_backend

# Store price histry for all available pairs
def get_price_history(asset_list, api):

    # Get prices and store in DataFrame
	price_history_dict = {}
	with alive_bar(0, title='Getting Price History...') as bar:
		Parallel(n_jobs=8, prefer="threads")(delayed(price_history_execution)(asset) for asset in asset_list)
		bar()

    # Return output
	return asset_list

def price_history_execution(asset):
	asset.klines = None
	counts = 0
	if counts < api.search_limit:
		get_price_klines(asset, api)
		if asset.klines is not None:
			lg.info("Successfully Stored Data For %s!" % asset.symbol)
			counts = counts + 1
		else:
			asset_list.remove(asset)
			lg.info("Unable To Store Data For %s! Removed From Asset List" % asset.symbol)
	return asset
