from func_stats import *
from config_strategy_api import *
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
	lg.info("Order Submitted!")

    # Return order
	return asset
    


# Initialise execution
def initialize_order_execution(asset):
	if asset.quantity > 0:
		order = place_order(asset)
	return asset
