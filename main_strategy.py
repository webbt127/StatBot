import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from func_get_symbols import get_tradeable_symbols
from func_prices_json import get_price_history
from func_cointegration import get_cointegrated_pairs
#from func_plot_trends import plot_trends
import pandas as pd
import json
from logger import *

initialize_logger()

"""STRATEGY CODE"""
if __name__ == "__main__":
    

    # # STEP 1 - Get list of symbols
    print("Getting symbols...")
    sym_response = get_tradeable_symbols()

    # # STEP 2 - Construct and save price history
    print("Constructing and saving price data to JSON...")
    if len(sym_response) > 0:
        price_dict = get_price_history(sym_response)

    # # STEP 3 - Find Cointegrated pairs
    print("Calculating co-integration...")
    if len(price_dict) > 0:
        coint_pairs = get_cointegrated_pairs(price_dict)
