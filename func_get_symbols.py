from config_strategy_api import session

# Get symbols that are tradeable
def get_tradeable_symbols():

    # Get available symbols
    active_assets = session.list_assets(status='active')
    asset_list = [a for a in active_assets if a.easy_to_borrow == True and a.tradable == True and getattr(a, 'class') == 'us_equity']
    print(asset_list)

    # Return ouput
    return asset_list
