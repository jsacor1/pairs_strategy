import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import toolkit as tk
import os

def sq_differences(normalized_v):
    """
    Creates a symmetrical matrix in which each value represents the squared difference between column i and index i.
    This function was created for the pairs_strategy() function
    """
    #creating a dataframe of n stocks * n stocks
    sqdiff_df = pd.DataFrame(columns=normalized_v.columns, index=normalized_v.columns)
    # filling up the empty dataframe with the squared differences.
    for c in sqdiff_df.columns:
        for i in sqdiff_df.index:
            ticker_c_normalisedP = normalized_v[c]
            ticker_i_normalisedP = normalized_v[i]
            sqdiff_ic = ((ticker_c_normalisedP - ticker_i_normalisedP)**2).sum()
            sqdiff_df.loc[i,c] = sqdiff_ic
    
    return sqdiff_df

def results_df_pairs_strategy(pairs, normalized, r, start_period, testing_period, trading_period, signal_pos, signal_close):
    """
    Creates a dataframe of the results. It includes the pairs traded, spread, a flag of when a positions should be opened and closed,
    the return of each pair traded, among others.
    This function was created for the pairs_strategy() function
    """
    # Calculating the spread to compare against signal
    # checking if it is needed to normalize again when the trading period starts.
    index_start = r.iloc[start_period+testing_period:min(start_period+testing_period+trading_period, r.shape[0])].index[0]
    index_end = r.iloc[start_period+testing_period:min(start_period+testing_period+trading_period, r.shape[0])].index[-1]
    if normalized:
        normalized_p = (r.iloc[start_period+testing_period:min(start_period+testing_period+trading_period, r.shape[0])]+1).cumprod()
        #normalized_p_all is an extended dataframe in case there are open positions at the end of the trading period
        normalized_p_all = (r.iloc[start_period+testing_period:]+1).cumprod()
    else:
        normalized_p = (r.iloc[start_period:min(start_period+testing_period+trading_period, r.shape[0])]+1).cumprod()
        #normalized_p_all is an extended dataframe in case there are open positions at the end of the trading period
        normalized_p_all = (r.iloc[start_period:]+1).cumprod()
           
    #normalized_p = normalized_p.iloc[start_period+testing_period:min(start_period+testing_period+trading_period, r.shape[0])]
    normalized_p = normalized_p.loc[index_start:index_end]
    
    #normalized_p_all is an extended dataframe in case there are open positions at the end of the trading period
    normalized_p_all = normalized_p_all.loc[index_start:]
    #normalized_p_all = normalized_p_all.iloc[start_period+testing_period:]
    #creating a df to store results. First data I am adding is the pair tickers.
    results = pd.DataFrame(data=[np.repeat(pairs[0], normalized_p.shape[0]), np.repeat(pairs[1], normalized_p.shape[0])],
                index=["pair0", "pair1"], columns=normalized_p.index).T
    results["actual_spread"] = normalized_p[pairs[0]] - normalized_p[pairs[1]]
    results["abs_spread"] = abs(results["actual_spread"])
    results.eval("high_spread_per = abs_spread > @signal_pos", inplace=True)
        
    #analysis per date on the long/short positions taken and adding the results to the df of results
    open_pos = []
    len_open_pos = len(open_pos)
    for date in results.index[1:]:
        # if there is a signal to open a position, add 1 to the open_pos variable. 1 means there is an open position, nothing means
        # there is no open position
        if results.loc[date, "high_spread_per"] == True and 1 not in open_pos:
            open_pos.append(1)
        # when there is an active position and a signal to close it, remove the 1 from open_pos
        elif results.loc[date, "abs_spread"] < signal_close and 1 in open_pos:
            open_pos.remove(1)
        # adding a column that indicates whether there is an active position. len(open_pos) could only be 1 or 0.
        len_open_pos = len(open_pos)
        results.loc[date, "open_pos"] = len_open_pos
           
    # if the flag open_pos is active, then add more (rows) dates until the position is closed.
    while len_open_pos == 1 and results.index[-1] < normalized_p_all.index[-1]:
        bool_date = results.index[-1] == normalized_p_all.index
        index_date = np.where(bool_date == True)
        new_date = normalized_p_all.iloc[index_date[0]+1].index
        #new_date = normalized_p_all.loc[results.index[-1] == normalized_p_all.index.shift(-1, freq="D")].index
        actual_spread_new = normalized_p_all.loc[new_date, pairs[0]] - normalized_p_all.loc[new_date, pairs[1]]
        actual_spread_new = actual_spread_new[0]
        data = {"pair0": pairs[0], "pair1": pairs[1], "actual_spread": actual_spread_new,
                "abs_spread": abs(actual_spread_new), "high_spread_per": abs(actual_spread_new)>signal_pos}
        results = pd.concat([results, pd.DataFrame(data=data, index=new_date)], verify_integrity=True)
        #results = results.append(pd.DataFrame(data=data, index=new_date))
        
        #if there is a signal to close the position, update open_pos
        if abs(actual_spread_new) < signal_close:
            open_pos.remove(1)
            
        len_open_pos = len(open_pos)
        results.loc[new_date, "open_pos"] = len_open_pos
    
    # Calculating the returns of the strategy for the pair
    for date in results.index[1:]:
        # Shifting 1 day, because once we have a signal we would actually enter the position the next day when the market opens.
        if results.shift(1).loc[date,"open_pos"] == True:
            if results.shift(1).loc[date, "actual_spread"] > 0:
                # if spread is positive I need to go long on pairs[1] and short on pairs[0]
                results.loc[date, "pair0_ret"] = -r.loc[date, pairs[0]]
                results.loc[date, "pair1_ret"] = r.loc[date, pairs[1]]
            else:
                # if spread is positive I need to go short on MQY and long on MQT
                results.loc[date, "pair0_ret"] = rets.loc[date, pairs[0]]
                results.loc[date, "pair1_ret"] = -rets.loc[date, pairs[1]]
                
        else:
            # if the signal is False, then there are no positions being traded.
            results.loc[date, "pair0_ret"] = 0
            results.loc[date, "pair1_ret"] = 0
            
    return results


def pairs_strategy(r, testing_period=252, trading_period=125, n_pairs=10, std_spread_open=2, std_spread_close=0, normalized=False):
    """
    Trading strategy that selects the n pairs with the lowest squared differences in their normalized values. The strategy opens long
    and short positions per pair when a signal is triggered. The signal is triggered when the spread between the normalized values of
    the pair goes beyond a certain std, thus expecting the normalized values to converge to a normal value based on history.
    
    Description of the arguments:
    * r is a dataframe of the returns
    * testing_period is the period to be used to calculate the squared differences between each possible pair
    * trading period is the period used to trade the pairs created from the testing period
    * n_pairs refers to the top n pairs to be used (i.e. 20 pairs having the lowest squared differences-spread)
    * std_spread_open refers to the number of standard deviation the actual spread should be away from the historical mean spread in 
    order to create a signal.
    * std_spread_close refers to the number of std the actual spread should be away from the historical mean in order to close an 
    open position.
    * if normalized is True, every trading period the values are normalized again. If False, the values are normalized starting on 
    the testing period.
    """
    
    n_periods = r.shape[0]
    period = testing_period+trading_period
    start_period = 0
    final_results_dict = {}
    
    while start_period+testing_period < n_periods:
        normalized_p = (r.iloc[start_period:start_period+testing_period]+1).cumprod()
        #creating a symmetrical matrix with the squared differences per pair
        sqdiff_df = sq_differences(normalized_p)
        
        #Removing the zeros from the diagonal.
        sqdiff_df_nozero = sqdiff_df.query("@sqdiff_df>0")
        
        #finding top n pairs
        pairs_list = []
        for i in range(1,n_pairs+1):
            minv = sqdiff_df_nozero.min().min()
            pair_tickers = sqdiff_df_nozero[sqdiff_df_nozero == minv].sum()[sqdiff_df_nozero[sqdiff_df_nozero == minv].sum() == minv].index
            pairs_list.append([pair_tickers[0], pair_tickers[1]])
            sqdiff_df_nozero = sqdiff_df_nozero.query("@sqdiff_df_nozero != @minv")
        
        # Calculating the signal to open and close positions for each pair from the pairs_list
        signals = {}
        for pair in pairs_list:
            spread = normalized_p[pair[0]] - normalized_p[pair[1]] 
            mean = spread.mean()
            std = spread.std()
            signal_pos = mean + (std_spread_open*std)
            signal_close = mean + (std_spread_close*std)
            signals[str(pair)] = [signal_pos, signal_close]
            
        #Calculating the results of the backtest for each pair
        counter = 0
        dict_of_dict = {}
        for pair in pairs_list:
            results = results_df_pairs_strategy(pairs=pair, normalized=normalized, r=r, start_period=start_period,
                                                testing_period=testing_period, trading_period=trading_period, 
                                                signal_pos=signals[str(pair)][0], signal_close=signals[str(pair)][1])
        
            dict_of_dict[counter] = results
            counter += 1
        
        #Creating the keys for the dictionary where the results will be stored.
        trading_df = r.iloc[start_period+testing_period:min(start_period+testing_period+trading_period, r.shape[0])]    
        key_period = str(f"testing period: {normalized_p.index[0]} to {normalized_p.index[-1]}, trading period: {trading_df.index[0]} to {trading_df.index[-1]}")
        #adding dictionary of results to another dictionary
        final_results_dict[key_period] = dict_of_dict
        print(key_period)    
        start_period += trading_period
        
    return final_results_dict

def summary_stats(r, periods_per_year,riskfree_rate=0.03):
    """
    Return a DataFrame that contains aggregated summary stats for the returns in the columns of r
    """
    ann_r = r.aggregate(tk.annualize_rets, periods_per_year=periods_per_year)
    ann_vol = r.aggregate(tk.annualize_vol, periods_per_year=periods_per_year)
    ann_sr = r.aggregate(tk.sharpe_ratio, riskfree_rate=riskfree_rate, periods_per_year=periods_per_year)
    dd = r.aggregate(lambda r: tk.drawdown(r).Drawdown.min())
    hist_cvar5 = r.aggregate(tk.cvar_historic)
    return pd.DataFrame({
        "Annualized Return": ann_r,
        "Annualized Vol": ann_vol,
        "Historic CVaR (5%)": hist_cvar5,
        "Sharpe Ratio": ann_sr,
        "Max Drawdown": dd
    })
