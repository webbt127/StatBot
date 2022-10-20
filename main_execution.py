# Remove Pandas Future Warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# General Imports
from config_execution_api import *
from func_position_calls import *
from func_trade_management import *
from func_execution_calls import *
from func_close_positions import *
from func_get_zscore import *
import time
from func_execution_calls import *

class position:
	def __init__(self):
    		self.symbol = ""


""" RUN STATBOT """
if __name__ == "__main__":

        # Check if open trades already exist
		position_1 = position()
		position_2 = position()
		is_p_ticker_open = open_position_confirmation(signal_positive_ticker)
		is_n_ticker_open = open_position_confirmation(signal_negative_ticker)
		is_p_ticker_active = active_position_confirmation(signal_positive_ticker)
		is_n_ticker_active = active_position_confirmation(signal_negative_ticker)
		checks_all = [is_p_ticker_open, is_n_ticker_open, is_p_ticker_active, is_n_ticker_active]
		is_manage_new_trades = not any(checks_all)

        # Save status
		status_dict["message"] = "Initial checks made..."
		status_dict["checks"] = checks_all
		save_status(status_dict)

        # Check for signal and place new trades
		if is_manage_new_trades and kill_switch == 0:
			status_dict["message"] = "Managing new trades..."
			save_status(status_dict)
			kill_switch, signal_side = manage_new_trades(kill_switch)

        # Managing open kill switch if positions change or should reach 2
        # Check for signal to be false
		if kill_switch == 1:

            # Get and save the latest z-score
			zscore, signal_sign_positive = get_latest_zscore()

            # Close positions
			if signal_side == "positive" and zscore < 0:
				kill_switch = 2
			if signal_side == "negative" and zscore >= 0:
				kill_switch = 2

            # Put back to zero if trades are closed
			if is_manage_new_trades and kill_switch != 2:
				kill_switch = 0

        # Close all active orders and positions
		if kill_switch == 2:
			print("Closing all positions...")
			status_dict["message"] = "Closing existing trades..."
			save_status(status_dict)
			kill_switch = close_all_positions(kill_switch)

            # Sleep for 5 seconds
			time.sleep(5)
