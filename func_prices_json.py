from func_price_klines import get_price_klines
import json
from alive_progress import alive_bar
import logging as lg

# Store price histry for all available pairs
def get_price_history(asset_list):

    # Get prices and store in DataFrame
	counts = 0
	price_history_dict = {}
	with alive_bar(len(asset_list)) as bar:
		for asset in asset_list:
			price_history = get_price_klines(asset.symbol)
			if price_history is not None:
				asset.price_history = price_history
				counts += 1
				lg.info("Successfully Stored Data For %s!" % asset.symbol)
			else:
				asset_list.remove(asset.symbol)
				lg.info("Unable To Store Data For %s! Removed From Asset List" % asset.symbol)
			bar()

    # Return output
return asset_list
