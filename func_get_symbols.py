from config_strategy_api import *

# Get symbols that are tradeable
def get_tradeable_symbols():

    # Get available symbols
    active_assets = api.session.list_assets(status='active')
    global asset_list = [a for a in active_assets if a.easy_to_borrow == True and a.tradable == True and getattr(a, 'class') == 'us_equity']

    # Return ouput
    return asset_list
