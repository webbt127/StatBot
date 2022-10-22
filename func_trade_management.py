from config_execution_api import *
from func_price_calls import *
from func_get_zscore import *
from func_execution_calls import *
from func_order_review import *
import time

# Manage new trade assessment and order placing
def manage_new_trades(position_1, position_2):

    # Set variables
	order_long_id = ""
	order_short_id = ""
	signal_side = ""
	hot = False

    # Get and save the latest z-score
	zscore, signal_sign_positive = get_latest_zscore()

    # Switch to hot if meets signal threshold
    # Note: You can add in coint-flag check too if you want extra vigilence
	if abs(zscore) > api.signal_trigger_thresh:

        # Active hot trigger
		hot = True
		print("-- Trade Status HOT --")
		print("-- Placing and Monitoring Existing Trades --")

    # Place and manage trades
	if hot  == 0:

        # Get trades history for liquidity
		get_ticker_trade_liquidity(position_2)
		get_ticker_trade_liquidity(position_1)

        # Determine long ticker vs short ticker
		if signal_sign_positive:
			long_ticker = position_2.symbol
			short_ticker = position_1.symbol
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

        # Fill targets
		capital_long = api.tradeable_capital_usdt * 0.5
		capital_short = api.tradeable_capital_usdt - capital_long
		initial_fill_target_long_usdt = avg_liquidity_long * last_price_long
		initial_fill_target_short_usdt = avg_liquidity_short * last_price_short
		initial_capital_injection_usdt = min(initial_fill_target_long_usdt, initial_fill_target_short_usdt)

        # Ensure initial cpaital does not exceed limits set in configuration
		if limit_order_basis:
			if initial_capital_injection_usdt > capital_long:
				initial_capital_usdt = capital_long
			else:
				initial_capital_usdt = initial_capital_injection_usdt
		else:
			initial_capital_usdt = capital_long

        # Set remaining capital
		remaining_capital_long = capital_long
		remaining_capital_short = capital_short

        # Trade until filled or signal is false
		order_status_long = ""
		order_status_short = ""
		counts_long = 0
		counts_short = 0

            # Place order - long
		if counts_long == 0:
			order_long_id = initialise_order_execution(long_ticker, "Long", initial_capital_usdt)
			counts_long = 1 if order_long_id else 0
			remaining_capital_long = remaining_capital_long - initial_capital_usdt

            # Place order - short
		if counts_short == 0:
			order_short_id = initialise_order_execution(short_ticker, "Short", initial_capital_usdt)
			counts_short = 1 if order_short_id else 0
			remaining_capital_short = remaining_capital_short - initial_capital_usdt

            # Update signal side
		if zscore > 0:
			signal_side = "postive"
		else:
			signal_side = "negative"

            # Allow for time to register the limit orders
		time.sleep(3)

            # Check limit orders and ensure z_score is still within range
		zscore_new, signal_sign_p_new = get_latest_zscore()
		if abs(zscore_new) > signal_trigger_thresh * 0.9 and signal_sign_p_new == signal_sign_positive:

                    # Check long order status
			if counts_long == 1:
				order_status_long = check_order(long_ticker, order_long_id, remaining_capital_long, "Long")

                    # Check short order status
			if counts_short == 1:
				order_status_short = check_order(short_ticker, order_short_id, remaining_capital_short, "Short")

			print(order_status_long, order_status_short, zscore_new)

                    # If orders still active, do nothing
			if order_status_long == "Order Active" or order_status_short == "Order Active":
				continue

                    # If orders partial fill, do nothing
			if order_status_long == "Partial Fill" or order_status_short == "Partial Fill":
				continue

                    # If position filled - place another trade
			if order_status_long == "Position Filled" and order_status_short == "Position Filled":
				counts_long = 0
				counts_short = 0

                    # If order cancelled for long - try again
			if order_status_long == "Try Again":
				counts_long = 0

                    # If order cancelled for short - try again
			if order_status_short == "Try Again":
				counts_short = 0

			else:
                    # Cancel all active orders
				session_private.cancel_all_active_orders(symbol=signal_positive_ticker)
				session_private.cancel_all_active_orders(symbol=signal_negative_ticker)

    # Output status
    return signal_side
