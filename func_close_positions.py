from config_execution_api import signal_positive_ticker
from config_execution_api import signal_negative_ticker
from config_execution_api import session_private

# Get position information
def get_position_info(ticker):

    # Declare output variables
	side = 0
	size = ""

    # Extract position info
	try:
		position = session_private.get_position(ticker)
		size = int(position.qty)
		if size > 0:
			side = "Buy"
		else:
			side = "Sell"
	except Exception as e:
		#lg.info("No Existing Position For %s!" % asset.symbol)
		size = 0
		side = "Sell"

    # Return output
	return side, size


#  Place market close order
def place_market_close_order(ticker, side, size):

    # Close position
	session_private.submit_order(
		symbol=ticker,
		side=side,
		type='market',
		qty=size,
		time_in_force="gtc"
	)

    # Return
	return


# Close all positions for both tickers
def close_all_positions(kill_switch):

    # Cancel all active orders
	session_private.cancel_all_orders()

    # Get position information
	side_1, size_1 = get_position_info(signal_positive_ticker)
	side_2, size_2 = get_position_info(signal_negative_ticker)

	if size_1 > 0:
		place_market_close_order(signal_positive_ticker, side_2, size_1) # use side 2

	if size_2 > 0:
		place_market_close_order(signal_negative_ticker, side_1, size_2) # use side 1

    # Output results
	kill_switch = 0
	return kill_switch
