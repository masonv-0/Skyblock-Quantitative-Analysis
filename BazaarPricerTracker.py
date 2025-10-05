import sys
import requests as rq
import pandas as pd
import numpy as np
from datetime import datetime as dt, timedelta as td
import matplotlib.pyplot as plt

def sortAllItems():
    itemUrl = "https://sky.coflnet.com/api/items/bazaar/tags"

    response = rq.get(itemUrl, timeout = 10)
    response.raise_for_status
    report = response.json()

    sufficientVolumeItems = list()

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
                #sufficientVolumeItems.append(dataframe["productId"])
        
        #print(sufficientVolumeItems)

# Grab the last week worth of data on the item
def getItemData(itemTag, timeframe, timestampFormat):
    url = "https://sky.coflnet.com/api/bazaar/" + itemTag + timeframe

    response = rq.get(url, timeout = 10)
    response.raise_for_status()
    report = response.json()

    dataframe = pd.json_normalize(report)
    dataframe.loc[:, timestampFormat] = pd.to_datetime(dataframe[timestampFormat])

    return dataframe

def removeDailyData(dataframe):
    yesterday = dt.now() - td(1)
    dataframe = dataframe[dataframe["timestamp"] <= yesterday]

def analyzePrice(week, current, itemTag):
    weekAverageBuy = week["buy"].mean()
    weekSTDBuy = week["buy"].std()

    weekBenchmarkPrice = round((weekAverageBuy + (0.5 * weekSTDBuy)),2)
    buyOrderPrice = round((float(current["sellPrice"][0] + 0.1)),2)

    percentDifference = round((100 * (weekBenchmarkPrice - buyOrderPrice) / weekBenchmarkPrice), 2)

    if (buyOrderPrice <= weekBenchmarkPrice - (0.1 * weekBenchmarkPrice)):
        print(itemTag + " is worth buying at -",percentDifference,"% from the past week.")
    else:
        if (percentDifference >= 0):
            print(itemTag + " is not worth buying at -",percentDifference,"% from the past week.")
        else:
            print(itemTag + " is not worth buying at +",abs(percentDifference),"% from the past week.")
    
    print("Current Buy Order Price:",buyOrderPrice)
    print("Weekly Benchmark Price:",weekBenchmarkPrice)

    #plotData(week, weekBenchmarkPrice, buyOrderPrice, itemTag)

def plotData(week, benchmark, buyOrder, itemTag):
    week = week.sort_values("timestamp")

    plt.figure(figsize = (15,10))
    title = itemTag + " History"
    plt.title(title)
    plt.ylabel("Price")
    plt.xlabel("Time")

    plt.plot(week["timestamp"], week["buy"])
    plt.plot(week["timestamp"], week["sell"])
    plt.axhline(y = benchmark, color = "green", linestyle = "--")
    plt.axhline(y = buyOrder, color = "red", linestyle = "--")
    plt.ticklabel_format(style="plain", axis="y")

    plt.show()

def checkStrategyHistory(itemTag):
    # Getting item data into a dataframe, reversing it because it starts with the most recent dates
    url = "https://sky.coflnet.com/api/bazaar/" + itemTag + "/history"
    response = rq.get(url, params = {"start": "2021-01-01T00:00:00"},timeout = 10)
    response.raise_for_status
    report = response.json()
    dataframe = pd.json_normalize(report)
    # Reverse row order
    dataframe = dataframe.iloc[::-1].reset_index(drop=True)
    dataframe = dataframe.dropna().reset_index(drop=True)

    # Determining target price for each day
    dataframe["previousWeekAverage"] = dataframe["buy"].rolling(window = 7).mean()
    dataframe["previousWeekSTD"] = dataframe["buy"].rolling(window = 7).std()
    dataframe["targetPrice"] = 0.9 * (dataframe["previousWeekAverage"] + 0.5 * dataframe["previousWeekSTD"])

    # Determining position and signal for each day
    dataframe["position"] = np.where(dataframe["targetPrice"] >= (dataframe["sell"] + 0.1), 1, 0)
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

        if not sellTrades.empty:
            sellPrice = ((sellTrades.iloc[0])["buy"]) - 0.1

            profit = quantity * (sellPrice - buyPrice)
            invested = quantity * buyPrice

            totalItemProfit += profit
            totalItemInvested += invested

            #print(f"Bought {quantity} " + itemTag + f" for {buyPrice:.2f}, sold {quantity} " + itemTag + f" for {sellPrice:.2f}, profit = {profit:.2f}, Date: {date}")
        else:
            #print("No sell signal found")
            pass

    roi = totalItemProfit / totalItemInvested * 100
    totalProfitList.append(totalItemProfit)
    totalInvestedList.append(totalItemInvested)
    print(f"------- {itemTag} -------")
    print(f"Total profit: {totalItemProfit:.2f}, Total invested: {totalItemInvested:.2f}")
    print(f"Return on Investment: {roi:.2f}%")
    print()

# Items with sufficient volume, price, and spread as checked on 9/31
targetItems = [
    "FUMING_POTATO_BOOK",
    "RECOMBOBULATOR_3000",
    "DRAGON_HORN",
    "DRAGON_CLAW",
    "SUPERIOR_FRAGMENT",
    "DEEP_SEA_ORB",
    "SHADOW_WARP_SCROLL",
    "GIANT_FRAGMENT_DIAMOND",
    "WITHER_BLOOD",
    "PRECURSOR_GEAR",
    "COLOSSAL_EXP_BOTTLE",
    "SPIRIT_BONE",
    "SPIRIT_WING",
    "GIANT_TOOTH",
    "MAGMA_BUCKET",
    "AOTE_STONE",
    "PLASMA_BUCKET",
    "DARK_ORB",
    "ENCHANTED_LAVA_BUCKET",
    "ENCHANTED_DIAMOND_BLOCK",
    "CRYSTAL_FRAGMENT",
    "ENCHANTED_HOPPER"
]

operation = int(input("What would you like to do? "
"|1| Check Target Flips "
"|2| Check Target Items "
"|3| Check Strategy History"))
match operation:
    case 1:
        for item in targetItems:
            weeklyDF = getItemData(item, "/history/week", "timestamp")
            currentDF = getItemData(item, "/snapshot", "timeStamp")
            removeDailyData(weeklyDF)
            analyzePrice(weeklyDF, currentDF, item)
    case 2:
        sortAllItems()
    case 3:
        totalProfitList = []
        totalInvestedList = []
        for item in targetItems:
            checkStrategyHistory(item)
        totalProfit = sum(totalProfitList)
        totalInvested = sum(totalInvestedList)
        print(f"Total Profit for all items: {totalProfit:.2f}")
        print(f"Total Invested for all items: {totalInvested:.2f}")
        print(f"Total ROI for all items: {(totalProfit/totalInvested):.2f}")
    case _:
        print("Invalid Option!")
        sys.exit(0)

# Things to add:
# - Test different volume metrics for quantity to see what gets the highest total ROI
# - First strategy to compare: sell condition is a 10% profit increase from the buy price
# - Factor in tax (?)
# - Sort by highest profit/percentage margin