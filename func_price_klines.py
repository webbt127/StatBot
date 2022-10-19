"""
    interval: Min, Hour, Day, Week and Month time window sizes with a maximum constraint on the values: 59Min, 23Hour, 1Day, 1Week, 12Month
    from: integer from timestamp in seconds
    limit: max size of 200
"""

from config_strategy_api import *
from main_strategy import *
from alpaca_trade_api.rest import TimeFrame
import datetime
import time

def get_start_time():
	time_start_date = 0
	if api.timeframe == 60:
		time_start_date = datetime.datetime.now() - datetime.timedelta(hours=kline_limit)
	if api.timeframe == "D":
		time_start_date = datetime.datetime.now() - datetime.timedelta(days=kline_limit)
	time_start = time_start_date.isoformat("T") + "Z"
	return time_start

# Get historical prices (klines)
def get_price_klines(asset):

    # Get prices
    try:
        asset.klines = api.session.get_bars(
            symbol = asset.symbol,
            timeframe = TimeFrame.Hour,
            limit = api.kline_limit,
            start = get_start_time()
        ).df
    except Exception as e:
        print("Could Not Get Prices")
        return

    # Manage API calls
    #time.sleep(0.15)

    # Return output
    return asset
