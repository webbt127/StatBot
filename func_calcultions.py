from config_execution_api import stop_loss_fail_safe
from config_execution_api import ticker_1
from config_execution_api import rounding_ticker_1
from config_execution_api import rounding_ticker_2
from config_execution_api import quantity_rounding_ticker_1
from config_execution_api import quantity_rounding_ticker_2
import math


# Get trade details and latest prices
def get_trade_details(orderbook, direction="Long", capital=0):

    # Set calculation and output variables
    price_rounding = 20
    quantity_rounding = 20
    mid_price = 0
    quantity = 0
    stop_loss = 0

    # Get prices, stop loss and quantity
    if orderbook:

        # Set price rounding
        price_rounding = rounding_ticker_1 if orderbook.symbol == ticker_1 else rounding_ticker_2
        quantity_rounding = quantity_rounding_ticker_1 if orderbook.symbol == ticker_1 else quantity_rounding_ticker_2

            # Get nearest ask, nearest bid and orderbook spread
        nearest_ask = orderbook.ap
        nearest_bid = orderbook.bp

            # Calculate hard stop loss
        if direction == "Long":
            mid_price = nearest_bid # placing at Bid has high probability of not being cancelled, but may not fill
            stop_loss = round(mid_price * (1 - stop_loss_fail_safe), price_rounding)
        else:
            mid_price = nearest_ask  # placing at Ask has high probability of not being cancelled, but may not fill
            stop_loss = round(mid_price * (1 + stop_loss_fail_safe), price_rounding)

            # Calculate quantity
        if mid_price > 0:
            quantity = round(capital / mid_price, quantity_rounding)
        else:
            quantity = 0

    # Output results
    return (mid_price, stop_loss, quantity)
