from func_calcultions import *
import pandas as pd


class Orderbook():
	pass


# Place limit or market order
def place_order(asset):

    # Set variables
	if asset.direction == "Long":
		asset.side = "Buy"
	else:
		asset.side = "Sell"

    # Place limit order
	if api.limit_order_basis:
		asset.order = api.session.submit_order(
			symbol=asset.symbol,
			side=asset.side,
			type="limit",
			qty=asset.quantity,
			take_profit=dict(limit_price=asset.price),
			time_in_force="gtc",
			stop_loss=dict(stop_price=asset.stop_loss, limit_price=asset.stop_loss)
		)
	else:
		asset.order = api.session.submit_order(
			symbol=asset.symbol,
			side=asset.side,
			order_type='market',
			qty=asset.quantity,
			time_in_force="gtc",
			stop_loss=dict(stop_price=asset.stop_loss, limit_price=asset.stop_loss)
		)

    # Return order
	return asset
    


# Initialise execution
def initialize_order_execution(asset, capital):
	asset.orderbook = Orderbook()
	asset.latest_quote = api.session.get_latest_quote(asset.symbol)
	asset.orderbook.ap = getattr(asset.latest_quote, 'ap')
	asset.orderbook.bp = getattr(asset.latest_quote, 'bp')
	if asset.orderbook:
		get_trade_details(asset, capital)
		if asset.quantity > 0:
			order = place_order(asset)
			if "id" in order.keys():
				asset.order_id = order["id"]
	return asset
