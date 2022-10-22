import math


# Get trade details and latest prices
def get_trade_details(asset, capital=0):

    # Set calculation and output variables
    asset.price_rounding = 20
    asset.quantity_rounding = 20
    asset.mid_price = 0
    asset.quantity = 0
    asset.stop_loss = 0

    # Get prices, stop loss and quantity
    if asset.orderbook:

        # Set price rounding
        asset.price_rounding = api.rounding_ticker_1 if orderbook.symbol == api.ticker_1 else api.rounding_ticker_2
        asset.quantity_rounding = api.quantity_rounding_ticker_1 if orderbook.symbol == api.ticker_1 else api.quantity_rounding_ticker_2

            # Calculate hard stop loss
        if asset.direction == "Long":
            asset.mid_price = asset.orderbook.bp # placing at Bid has high probability of not being cancelled, but may not fill
            asset.stop_loss = round(asset.mid_price * (1 - api.stop_loss_fail_safe), api.price_rounding)
        else:
            asset.mid_price = asset.orderbook.ap  # placing at Ask has high probability of not being cancelled, but may not fill
            asset.stop_loss = round(asset.mid_price * (1 + api.stop_loss_fail_safe), api.price_rounding)

            # Calculate quantity
        if asset.mid_price > 0:
            asset.quantity = round(capital / asset.mid_price, asset.quantity_rounding)
        else:
            asset.quantity = 0

    # Output results
    return asset
