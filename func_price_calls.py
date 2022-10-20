from config_execution_api import *
#from func_calcultions import extract_close_prices
import datetime
import time


# Get trade liquidity for ticker
def get_ticker_trade_liquidity(ticker):

    # Get trades history
    trades = api.session.get_trades(
        symbol=ticker.symbol,
        limit=50
    )

    # Get the list for calculating the average liquidity
    quantity_list = []
    if "result" in trades.keys():
        for trade in trades["result"]:
            quantity_list.append(trade["qty"])

    # Return output
    if len(quantity_list) > 0:
        avg_liq = sum(quantity_list) / len(quantity_list)
        res_trades_price = float(trades["result"][0]["price"])
        return (avg_liq, res_trades_price)
    return (0, 0)


# Get start times
def get_timestamps():
    time_start_date = 0
    time_next_date = 0
    now = datetime.datetime.now()
    if timeframe == 60:
        time_start_date = now - datetime.timedelta(hours=kline_limit)
        time_next_date = now + datetime.timedelta(seconds=30)
    if timeframe == "D":
        time_start_date = now - datetime.timedelta(days=kline_limit)
        time_next_date = now + datetime.timedelta(minutes=1)
    time_start_seconds = int(time_start_date.timestamp())
    time_now_seconds = int(now.timestamp())
    time_next_seconds = int(time_next_date.timestamp())
    return (time_start_seconds, time_now_seconds, time_next_seconds)
