from func_price_klines import get_price_klines
import json
from alive_progress import alive_bar

# Store price histry for all available pairs
def store_price_history(symbols):

    # Get prices and store in DataFrame
    counts = 0
    price_history_dict = {}
    with alive_bar(len(symbols)) as bar:
        for sym in symbols:
            symbol_name = sym.symbol
            price_history = get_price_klines(symbol_name)
            if 'c' in price_history:
                price_history_dict[symbol_name] = price_history
                counts += 1
                print(f"{counts} items stored")
            else:
                print(f"{counts} items not stored")
            bar()

    # Output prices to JSON
    if len(price_history_dict) > 0:
        with open("1_price_list.json", "w") as fp:
            json.dump(price_history_dict, fp, indent=4)
        print("Prices saved successfully.")

    # Return output
    return
