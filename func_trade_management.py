from func_price_calls import *
from func_cointegration import *
from func_execution_calls import *
from func_order_review import *
import time

# Manage new trade assessment and order placing
def manage_new_trades(position_1, position_2):
    # Get and save the latest z-score
	get_trade_details(position_1, api.initial_capital_usdt)
	get_trade_details(position_2, api.initial_capital_usdt)
	zscore = get_latest_zscore(position_1, position_2)
	
	if zscore > 0:
		position_1.direction = "Short"
		position_2.direction = "Long"
	else:
		position_1.direction = "Long"
		position_2.direction = "Short"

    # Switch to hot if meets signal threshold
    # Note: You can add in coint-flag check too if you want extra vigilence
	if abs(zscore) > api.signal_trigger_thresh:

        # Get trades history for liquidity
		get_ticker_trade_liquidity(position_2)
		get_ticker_trade_liquidity(position_1)

        # Determine long ticker vs short ticker
		if zscore > 0:
			long_ticker = position_2
			short_ticker = position_1
			avg_liquidity_long = position_2.liquidity
			avg_liquidity_short = position_1.liquidity
			last_price_long = position_2.last_price
			last_price_short = position_1.last_price
		else:
			long_ticker = position_1.symbol
			short_ticker = position_2.symbol
			avg_liquidity_long = position_1.liquidity
			avg_liquidity_short = position_2.liquidity
			last_price_long = position_1.last_price
			last_price_short = position_2.last_price

		order_long_id = initialize_order_execution(long_ticker, "Long", api.initial_capital_usdt)
		order_short_id = initialize_order_execution(short_ticker, "Short", api.initial_capital_usdt)


    # Output status
	return
