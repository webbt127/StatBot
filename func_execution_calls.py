from func_stats import *
import logging as lg
from config_strategy_api import *
import pandas as pd


class Orderbook():
	pass


# Place limit or market order
def place_order(asset):

    # Set variables
	if asset.direction == "Long":
		asset.side = "buy"
	else:
		asset.side = "sell"

    # Place limit order
	if api.limit_order_basis:
		try:
			asset.order = api.session.submit_order(
				symbol=asset.symbol,
				side=asset.side,
				type="limit",
				qty=asset.quantity,
				limit_price=asset.mid_price,
				time_in_force='day',
				stop_loss=dict(stop_price=asset.stop_loss, limit_price=asset.stop_loss),
				extended_hours=True
			)
		except Exception as e:
			lg.info(e)
	else:
		try:
			asset.order = api.session.submit_order(
				symbol=asset.symbol,
				side=asset.side,
				order_type='market',
				qty=asset.quantity,
				time_in_force="day",
				stop_loss=dict(stop_price=asset.stop_loss, limit_price=asset.stop_loss)
			)
		except Exception as e:
			lg.info(e)
	lg.info("Order Submitted!")

    # Return order
	return asset
    


# Initialise execution
def initialize_order_execution(asset):
	if hasattr(asset, 'quantity'):
		if asset.quantity > 0:
			order = place_order(asset)
		else:
			lg.info("Quantity is set to zero!")
	else:
		lg.info("Quantity has not been calculated!")
	return asset
