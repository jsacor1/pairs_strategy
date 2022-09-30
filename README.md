# Pairs Strategy

## Logic

The logic behind the pairs strategy is that stocks that have tended to move together historically will generally continue moving together. When a certain pair starts diverging, one would expect the stocks to converge again. This reasoning allows the possibility of opening both long and short positions to make a riskless profit: one can short the stock that increased in price and buy the stock that decreased in price. In theory, one would not need any investment because the funds from the short position would be used to cover the long position.  

## Methodology

In this project, 700 hundred stocks were analysed. Of those stocks, the 10 pairs of stocks that move the most similarly were selected. The process is as follows:

1.	The price actions of all stocks for a period of 1 year (252 days) is normalised, assuming that in day 0 the value of all the stocks is 1. Then the return of the day over 1 year was added.
2.	Then, for every possible pair of stocks, the squared differences in their normalised values taken from step 1 are computed. Those squared differences are then added up. From this step, the output is a matrix showing the sum of the squared differences of the normalised values among every possible pair of stocks.
3.	The top 10 pairs with the lowest values in the matrix are selected. In addition, I calculated the mean and standard deviation of the squared differences for each pair of stock throughout the year.
4.	The top 10 pairs are traded for the following 6 months (125 days). Every day during those 6 months, the squared differences of the normalised values continue to be computed. There is a signal to open both long and short positions when the squared difference of the normalised value of a certain day is higher than two times the standard deviation plus the average squared differences of the last year (This data was computed in step 3). 
5.	There is a signal to close an open position when the squared differences of the normalised value equal the average squared differences of the last year. 
6.	I repeat these steps after the 125 days (6 months) are over.

## Key Takeaways, challenges, and future development

*	There are pairs that never converge, leading to relatively large drawdowns in some pairs.
*	There are pairs that converge after several years. There is a visual representation of this phenomenon in the below graph (time period from 1996 to 2004):

 ![image](https://user-images.githubusercontent.com/114669230/193101144-601966b8-90be-46e0-a765-686ca1e406ae.png)

*	As can be seen from the graph above, the best trades are the ones in which there is a signal to close the position within 400 hundred days (vertical blue line). There is a strong relationship between the number of days of trading and the return, sharpe ratio, and max drawdown. 
*	Based on the above results, I discovered that automatically closing the positions when they’ve been trading for over 800 hundred days can reduce the risk of the strategy. The likelihood of those pairs converging is really low and we minimise the losses of the strategy.
*	The strategy was tweaked based on the above findings, resulting in a huge improvement (2004-2021):

![image](https://user-images.githubusercontent.com/114669230/193105411-d9cdf207-866b-4f70-9481-30cf3a6c6b21.png)

*	The strategy has potential, but more research must be done. One must find the optimal number of days in which to automatically close a position to maximise the returns and minimise the potential drawdowns. In addition, one could do research to see if a stop loss could work rather than closing a position based on trading days. 
* Additionally, one major drawback in live implementation is the spread among pairs that have low liquidity. Some of the pairs that were selected by the algorithm have really low liquidity, meaning the spreads are huge; this factor reduces the margin of the trade. One should filter out stocks that have low liquidity because they tend not to be profitable in a live implementation of the strategy.   
