from config_strategy_api import session

# Get symbols that are tradeable
def get_tradeable_symbols():

    # Get available symbols
    symbols = session.list_assets(status='active')
    sym_list = [a for a in symbols if a.easy_to_borrow == True and a.tradable == True]

    # Return ouput
    print(sym_list)
    return sym_list

get_tradeable_symbols()
