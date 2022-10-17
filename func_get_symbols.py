from config_strategy_api import session

# Get symbols that are tradeable
def get_tradeable_symbols():

    # Get available symbols
    symbols = session.list_assets(status='active')
    sym_list = [a for a in symbols if (a.easy_to_borrow == True and a.tradable == True and a.class == 'us_equity')]

    # Return ouput
    return sym_list
