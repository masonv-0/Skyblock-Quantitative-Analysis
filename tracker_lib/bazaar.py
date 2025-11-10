import requests as rq
import pandas as pd
import numpy as np
from datetime import datetime as dt, timedelta as td
import matplotlib.pyplot as plt

"""
Parameters: None

Function: parses all items on the bazaar to find expensive items with a reasonable spread and high volume of orders. Prints the items as it finds them

Returns: None
"""
def sortAllItems():
    itemUrl = "https://sky.coflnet.com/api/items/bazaar/tags"

    response = rq.get(itemUrl, timeout = 10)
    response.raise_for_status
    report = response.json()

    for item in report:
        volumeUrl = "https://sky.coflnet.com/api/bazaar/" + item + "/snapshot"

        itemResponse = rq.get(volumeUrl, timeout = 10)
        itemReport = itemResponse.json()
        dataframe = pd.json_normalize(itemReport)
        if (("buyOrdersCount" in dataframe.columns) & ("sellOrdersCount" in dataframe.columns)):
            trueOrders = float((int(dataframe["buyOrdersCount"][0]) + int(dataframe["sellOrdersCount"][0])) / 2)
            truePrice = float((int(dataframe["buyPrice"][0]) + int(dataframe["sellPrice"][0])) / 2)
            trueSpread = float((int(dataframe["buyPrice"][0]) - int(dataframe["sellPrice"][0])) / 2)
            spreadThreshold = truePrice * 0.2
            if (((trueOrders >= 150.0) & (truePrice >= 50000.00)) & (trueSpread <= spreadThreshold)):
                print(dataframe["productId"])
        
"""
Parameters: item tag as it appears in Hypixel's backend (String), parameters for the API endpoint (String), timestamp format to be used when parsing data because it's slightly different for different endpoints (String)

Function: GETs data from the API endpoint, turns it into a dataframe, reformats timestamps for graphing purposes

Returns: bazaar data (pandas Dataframe)
"""
def getItemData(itemTag, timeframe, timestampFormat):
    url = "https://sky.coflnet.com/api/bazaar/" + itemTag + timeframe
    if (timeframe == "/history"):
        params = {}
        params["start"] = dt.now() - td(30)
        params["end"] = dt.now()
        response = rq.get(url, params, timeout = 10)
    else:
        response = rq.get(url, timeout = 10)
    response.raise_for_status()
    report = response.json()

    dataframe = pd.json_normalize(report)
    dataframe.loc[:, timestampFormat] = pd.to_datetime(dataframe[timestampFormat])

    return dataframe

"""
Parameters: dataframe from which to remove daily data (pandas Dataframe)

Function: removes the past 24 hours of bazaar data from the dataframe

Returns: None
"""
def removeDailyData(dataframe):
    yesterday = dt.now() - td(1)
    dataframe = dataframe[dataframe["timestamp"] <= yesterday]

"""
Parameters: items in which the user is currently invested (Dictionary)

Function: check if sell order would result in 10m coins or 15% profit, factoring in tax. Prints result.

Returns: None
"""
def checkInvestmentStatus(investments):
    if (not investments):
        print("No investments found!")
        return
    investmentItems = list(investments.keys())

    for item in investmentItems:
        url = "https://sky.coflnet.com/api/bazaar/" + item + "/snapshot"

        response = rq.get(url, timeout = 10)
        response.raise_for_status()
        report = response.json()

        dataframe = pd.json_normalize(report)
        # Pretty standard to put up a sell order at 0.1 coins below the current lowest
        sellOrderPrice = round(dataframe["buyPrice"].iloc[0] - 0.1, 2)

        purchasePrice = investments[item][0]
        purchaseQuantity = investments[item][1]
        # Total profit selling at current sell order price, factoring in tax
        profitCoins = round(.98875 * (sellOrderPrice * purchaseQuantity) - (purchasePrice * purchaseQuantity), 2) 
        profitPercentage = round((profitCoins / purchasePrice * 100) / purchaseQuantity, 2)
        
        # "Worth" selling if we make 10m+ or 15% profit
        if ((profitCoins >= 10000000) or (profitPercentage >= 15.0)):
            print(str(purchaseQuantity) + "x " + item + " at price " + str(sellOrderPrice) + " is worth selling | Bought for " + str(purchasePrice) + " | Profit: " + str(profitCoins) + " coins or " + str(profitPercentage) + "%")
        else:
            print(str(purchaseQuantity) + "x " + item + " at price " + str(sellOrderPrice) + " is NOT worth selling | Bought for " + str(purchasePrice) + " | Profit: " + str(profitCoins) + " coins or " + str(profitPercentage) + "%")

"""
Parameters: item tags of target items (List)

Function: determine whether each item is worth buying by checking a variety of factors. Prints the result.

Returns: None
"""
def analyzePrice(itemTags):
    
    for item in itemTags:
        print("\n------- " + item + " -------")
        monthlyDF = getItemData(item , "/history", "timestamp")
        currentDF = getItemData(item, "/snapshot", "timeStamp")

        # Remove today's data to account for any crazy changes recently
        removeDailyData(monthlyDF)

        # Standard deviation for buy order prices
        buyOrderSTD = monthlyDF["sell"].std()

        # Mean for buy order prices
        buyOrderMean = monthlyDF["sell"].mean()

        # High benchmark (check for weird spikes)
        benchmarkHigh = monthlyDF["sell"].max() - buyOrderSTD
        
        # Low benchmark (likely buy)
        benchmarkLow = monthlyDF["sell"].min() + 0.25 * buyOrderSTD

        # Current buy order price
        buyOrderPrice = round((float(currentDF["sellPrice"].iloc[0] + 0.1)),2)

        # Risk analysis: check how many times the item has been above a 15% profit threshold
        profitThreshold = 1.15 * buyOrderPrice
        monthlyDF["position"] = np.where(monthlyDF["buy"] >= profitThreshold, 1, 0)
        daysAboveThreshold = (monthlyDF["position"] == 1).sum()

        # Difference between past month mean and current price as a percentage
        percentDifference = round((buyOrderMean - buyOrderPrice) / buyOrderMean * 100, 2)
        
        # We only consider buying if the current price is below average
        if (buyOrderPrice <= buyOrderMean):
            print("\n" + item + " is " + str(percentDifference) + "% below the monthly average")
            
            # If the item has not been +15%, it's not worth buying
            if (daysAboveThreshold == 0):
                print("\n" + item + " is not worth buying right now.")
                continue
            
            # If the item has only had 1-2 notable peaks, it's probably not worth buying
            if ((daysAboveThreshold <= 2) and (profitThreshold >= benchmarkHigh)):
                print("\n" + item + " is probably not worth buying right now. Check the graph for unusual spikes.")

            # If the item is really low, it's probably worth buying but checking the graph is a good idea
            if (buyOrderPrice <= benchmarkLow):
                print("\n" + item + " is super low, could be a huge opportunity. Check the graph and see what's up.")

        else:
            if (percentDifference >= 0):
                print("\n" + item + " is not worth buying at -",percentDifference,"% from the past month.")
            else:
                print("\n" + item + " is not worth buying at +",abs(percentDifference),"% from the past month.")
    
        print("   - Current Buy Order Price:",buyOrderPrice)
        print("   - Mean Buy Order Price:",buyOrderMean)

        plot = (input("\nWould you like to plot the data for " + item + "? Y/N \n") == "Y")

        if (plot):
            plotData(item)
            quit = (input("Would you like to move on to the next item? Y/N: \n") == "N")
            if (quit):
                break

"""
Parameters: item tag (String)

Function: plots a line graph for the past month of price history, and includes a few indicators

Returns: None
"""
def plotData(itemTag):
    monthlyDF = getItemData(itemTag , "/history", "timestamp")
    currentDF = getItemData(itemTag, "/snapshot", "timeStamp")

    benchmark = monthlyDF["sell"].max() - monthlyDF["sell"].std()
    buyOrderPrice = round((float(currentDF["sellPrice"].iloc[0] + 0.1)),2)
    sellOrderPrice = round((float(currentDF["buyPrice"].iloc[0] - 0.1)),2)

    monthlyDF = monthlyDF.sort_values("timestamp")

    plt.figure(figsize = (15,10))
    title = itemTag + " History"
    plt.title(title)
    plt.ylabel("Price")
    plt.xlabel("Time")

    plt.plot(monthlyDF["timestamp"], monthlyDF["buy"])
    plt.plot(monthlyDF["timestamp"], monthlyDF["sell"])

    plt.axhline(y = benchmark, color = "blue", linestyle = "--")
    plt.text(x = 1.01, y = benchmark, s = "Benchmark", color = "black", va = "bottom", ha = "left", transform = plt.gca().get_yaxis_transform())

    plt.axhline(y = 1.15 * buyOrderPrice, color = "green", linestyle = "--")
    plt.text(x = 1.01, y = 1.15 * buyOrderPrice, s = "15% Profit", color = "black", va = "bottom", ha = "left", transform = plt.gca().get_yaxis_transform())

    plt.axhline(y = buyOrderPrice, color = "orange", linestyle = "--")
    plt.text(x = 1.01, y = buyOrderPrice, s = "Current Buy Price", color = "black", va = "bottom", ha = "left", transform=plt.gca().get_yaxis_transform())

    plt.axhline(y = sellOrderPrice, color = "red", linestyle = "--")
    plt.text(x = 1.01, y = sellOrderPrice, s = "Current Sell Price", color = "black", va = "bottom", ha = "left", transform = plt.gca().get_yaxis_transform())

    plt.ticklabel_format(style="plain", axis="y")

    plt.show()

"""
Parameters: item tags of current items (List)

Function: looks at how our current strategy would have performed in the past. I know this part is kind of a mess, but I wanted to keep it to show that I've at least thought about backtesting.

Returns: None
"""
def checkStrategyHistory(itemTags):
    totalProfitList = []
    totalInvestedList = []
    
    for item in itemTags:
        # Getting item data into a dataframe
        url = "https://sky.coflnet.com/api/bazaar/" + item + "/history"
        response = rq.get(url, params = {"start": "2021-01-01T00:00:00"},timeout = 10)
        response.raise_for_status()
        report = response.json()
        dataframe = pd.json_normalize(report)

        # Reverse row order, drop N/As
        dataframe = dataframe.iloc[::-1].reset_index(drop=True)
        dataframe = dataframe.dropna().reset_index(drop=True)

        # Determining target price for each day
        dataframe["previousMonthAverage"] = dataframe["buy"].rolling(window = 30).mean()
        dataframe["previousMonthSTD"] = dataframe["buy"].rolling(window = 30).std()
        dataframe["targetPrice"] = (0.9 * dataframe["previousMonthAverage"])

        # Determining position and signal for each day
        dataframe["position"] = np.where(dataframe["targetPrice"] >= (dataframe["sell"] + 0.1), 1, 
                                     np.where(1.2 * dataframe["targetPrice"] <= (dataframe["sell"] + 0.1),0, np.nan))
        dataframe["signal"] = dataframe["position"].diff()

        totalItemProfit = 0
        totalItemInvested = 0
        buySignal = (dataframe["signal"] == 1.0)
        sellSignal = (dataframe["signal"] == -1.0)

        for buyIndex, row in dataframe[buySignal].iterrows():
            buyPrice = (row["sell"] + 0.1)
            sellTrades = dataframe[sellSignal & (dataframe.index > buyIndex)]
            date = row["timestamp"]
            volume = (row["buyVolume"] + row["sellVolume"]) / 2
            quantity = volume // 2000
            if (quantity == 0):
                quantity = 1.0

            if not sellTrades.empty:
                # Sale tax is 1.125% for my account
                sellPrice = 0.98875 * ((sellTrades.iloc[0])["buy"]) - 0.1

                profit = quantity * (sellPrice - buyPrice)
                invested = quantity * buyPrice

                totalItemProfit += profit
                totalItemInvested += invested

                print(f"Bought {quantity} " + item + f" for {buyPrice * quantity:.2f}, sold {quantity} " + item + f" for {sellPrice * quantity:.2f}, profit = {profit:.2f}, Date: {date}")
            else:
                print("No sell signal found")
                pass
        if (totalItemInvested != 0):
            roi = totalItemProfit / totalItemInvested * 100
            totalProfitList.append(totalItemProfit)
            totalInvestedList.append(totalItemInvested)
            print(f"------- {item} -------")
            print(f"Total profit: {totalItemProfit:.2f}, Total invested: {totalItemInvested:.2f}")
            print(f"Return on Investment: {roi:.2f}%")
            print()
        else:
            print(item + " never met conditions for strategy")
    
    return totalProfitList, totalInvestedList

# Things to add:
# - More comprehensive risk assessment