from config_execution_api import session_private
from config_execution_api import limit_order_basis
#from config_ws_connect import ws_public
from func_calcultions import get_trade_details
import pandas as pd

# Set leverage
def set_leverage(ticker):

    return


# Place limit or market order
def place_order(ticker, price, quantity, direction, stop_loss):

    # Set variables
    if direction == "Long":
        side = "Buy"
    else:
        side = "Sell"

    # Place limit order
    if limit_order_basis:
        order = session_private.submit_order(
            symbol=ticker,
            side=side,
            type="limit",
            qty=quantity,
            take_profit=dict(limit_price=price),
            time_in_force="gtc",
            stop_loss=dict(stop_price=stop_loss, limit_price=stop_loss)
        )
    else:
        order = session_private.submit_order(
            symbol=ticker,
            side=side,
            order_type='market',
            qty=quantity,
            time_in_force="gtc",
            stop_loss=dict(stop_price=stop_loss, limit_price=stop_loss)
        )

    # Return order
    return order
    


# Initialise execution
def initialise_order_execution(ticker, direction, capital):
    quote = session_private.get_latest_quote(ticker)
    orderbook.symbol = ticker
    orderbook.ap = getattr(quote, 'ap')
    orderbook.bp = getattr(quote, 'bp')
    if orderbook:
        mid_price, stop_loss, quantity = get_trade_details(orderbook, direction, capital)
        if quantity > 0:
            order = place_order(ticker, mid_price, quantity, direction, stop_loss)
            if "result" in order.keys():
                if "order_id" in order["result"]:
                    return order["result"]["order_id"]
    return 0
