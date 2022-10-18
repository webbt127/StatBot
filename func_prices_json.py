from func_price_klines import get_price_klines
import json
from alive_progress import alive_bar
import logging as lg

# Store price histry for all available pairs
def get_price_history(symbols):

    # Get prices and store in DataFrame
    counts = 0
    price_history_dict = {}
    with alive_bar(len(symbols)) as bar:
        for sym in symbols:
            if counts < 200:
                symbol_name = sym.symbol
                price_history = get_price_klines(symbol_name)
                if price_history is not None:
                    price_history_dict[symbol_name] = price_history
                    counts += 1
                    lg.info("Successfully Stored Data For %s!" % sym.symbol)
                else:
                    lg.info("Unable To Store Data For %s!" % sym.symbol)
            bar()

    # Return output
    return price_history_dict
