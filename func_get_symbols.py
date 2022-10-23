from config_strategy_api import *

# Get symbols that are tradeable
def get_tradeable_symbols():

    # Get available symbols
    active_assets = api.session.list_assets(status='active')
    asset_list.symbols = [a for a in active_assets if a.easy_to_borrow == True and a.tradable == True and getattr(a, 'class') == 'us_equity' and a.exchange == 'NYSE']

    # Return ouput
    return asset_list
