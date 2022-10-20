import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from func_get_symbols import *
from func_prices_json import *
from func_cointegration import *
from config_strategy_api import *
#from func_plot_trends import plot_trends
import pandas as pd
import json
from logger import *

initialize_logger()

api = config()
api.session = REST(api_key, api_secret, api_url)

"""STRATEGY CODE"""
if __name__ == "__main__":
    

    # # STEP 1 - Get list of symbols
    lg.info("Getting symbols...")
    asset_list = get_tradeable_symbols(api)

    # # STEP 2 - Construct and save price history
    lg.info("Constructing and saving price data to JSON...")
    if len(asset_list) > 0:
        get_price_history(asset_list, api)

    # # STEP 3 - Find Cointegrated pairs
    lg.info("Calculating co-integration...")
    if len(asset_list) > 0:
        coint_pairs = get_cointegrated_pairs(asset_list)
        print(coint_pairs)
