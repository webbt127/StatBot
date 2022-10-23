from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import pandas as pd
import math


# Calculate Z-Score
def calculate_zscore(spread):
    df = pd.DataFrame(spread)
    mean = df.rolling(center=False, window=z_score_window).mean()
    std = df.rolling(center=False, window=z_score_window).std()
    x = df.rolling(center=False, window=1).mean()
    df["ZSCORE"] = (x - mean) / std
    return df["ZSCORE"].astype(float).values


# Calculate spread
def calculate_spread(series_1, series_2, hedge_ratio):
    spread = pd.Series(series_1) - (pd.Series(series_2) * hedge_ratio)
    return spread


# Calculate metrics
def calculate_metrics(series_1, series_2):
    coint_flag = 0
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]
    model = sm.OLS(series_1, series_2).fit()
    hedge_ratio = model.params[0]
    spread = calculate_spread(series_1, series_2, hedge_ratio)
    zscore_list = calculate_zscore(spread)
    if p_value < 0.5 and coint_t < critical_value:
        coint_flag = 1
    return (coint_flag, zscore_list.tolist())


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
