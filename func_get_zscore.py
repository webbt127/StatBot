from func_calculations import *
from func_price_calls import *
from func_stats import *

# Get latest z-score
def get_latest_zscore():

    # Get latest price history
    get_price_klines(position_1, api)
    get_price_klines(position_2, api)
    get_trade_details(position_1, capital)
    get_trade_details(position_2, capital)

    # Get z_score and confirm if hot
    if len(position_1.klines) > 0 and len(position_2.klines) > 0:

        # Replace last kline price with latest orderbook mid price
        position_1.klines = position_1.klines[:-1]
        position_2.klines = position_2.klines[:-1]
        position_1.klines.append(position_1.mid_price)
        position_2.klines.append(position_2.mid_price)

        # Get latest zscore
        _, zscore_list = calculate_metrics(position_1.klines, position_2.klines)
        zscore = zscore_list[-1]
        if zscore > 0:
            signal_sign_positive = True
        else:
            signal_sign_positive = False

        # Return output
        return (zscore, signal_sign_positive)

    # Return output if not true
    return
