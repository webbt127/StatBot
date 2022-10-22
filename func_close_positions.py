# Get position information
def get_position_info(asset):

    # Declare output variables
	asset.side = 0
	asset.size = ""

    # Extract position info
	try:
		asset.position = api.session.get_position(ticker)
		asset.size = int(asset.position.qty)
		if asset.size > 0:
			asset.side = "Buy"
		else:
			asset.side = "Sell"
	except Exception as e:
		#lg.info("No Existing Position For %s!" % asset.symbol)
		asset.size = 0
		asset.side = "Sell"

    # Return output
	return asset


#  Place market close order
def place_market_close_order(asset):

    # Close position
	api.session.submit_order(
		symbol=asset.symbol,
		side=asset.side,
		type='market',
		qty=asset.size,
		time_in_force="gtc"
	)

    # Return
	return


# Close all positions for both tickers
def close_all_positions(kill_switch):

    # Cancel all active orders
	api.session.cancel_all_orders()

    # Get position information
	side_1, size_1 = get_position_info(api.signal_positive_ticker)
	side_2, size_2 = get_position_info(api.signal_negative_ticker)

	if size_1 > 0:
		place_market_close_order(api.signal_positive_ticker, side_2, size_1) # use side 2

	if size_2 > 0:
		place_market_close_order(api.signal_negative_ticker, side_1, size_2) # use side 1

    # Output results
	kill_switch = 0
	return kill_switch
