import matplotlib.pyplot as plt
import requests as rq
import pandas as pd
from datetime import datetime as dt, timedelta as td

# ------- Credit to cofnlet/skycoflnet for all API endpoints used for auction data ------- # 

def cleanData(dataframe):
    averagePrice = dataframe["startingBid"].mean()
    standardDeviation = dataframe["startingBid"].std()
    low = averagePrice - (5 * standardDeviation)
    high = averagePrice + (5 * standardDeviation)
    return dataframe[dataframe["startingBid"].between(low,high)]

# Plot the past week of auctions and the average value
def plotWeek(dataframe, lowest, itemName):
    dataframe = cleanData(dataframe)
    medianPrice = dataframe["startingBid"].median()

    dataframe.loc[:, "start"] = pd.to_datetime(dataframe["start"])
    dataframe = dataframe.sort_values("start")

    plt.figure(figsize=(15,10))
    title = "Weekly History & Median for " + itemName
    plt.title(title)
    plt.ylabel("Price")
    plt.xlabel("Date")

    plt.plot(dataframe["start"],dataframe["startingBid"])
    plt.ticklabel_format(style="plain", axis="y")
    plt.scatter(lowest["start"],lowest["startingBid"], s = 5)
    plt.axhline(y = medianPrice, color = "red", linestyle = "--")
    plt.show()

# Remove any items from the past 24 hours in the past week of prices
def removeDailyItems(pastWeekDF):
    now = dt.now()
    startCol = pastWeekDF["start"]
    shift = td(1)
    yesterday = now - shift
    for i in range(len(startCol)):
        timestampString = startCol[i]
        timestampFormat = "%Y-%m-%dT%H:%M:%S"
        timestamp = dt.strptime(timestampString, timestampFormat)
        if (timestamp >= yesterday):
            pastWeekDF.drop(index = i, inplace = True)
            i -= 1
    return pastWeekDF

# Find if any items are selling for >=5% of their weekly average
def findPriceGaps(itemTags):
    for item in itemTags:
        lowestBINsURL = "https://sky.coflnet.com/api/auctions/tag/" + item + "/active/bin"
        pastWeekURL = "https://sky.coflnet.com/api/auctions/tag/" + item + "/sold"

        try:
            # Grabbing data for past week of auctions
            pastWeekResponse = rq.get(pastWeekURL, timeout = 10)
            pastWeekResponse.raise_for_status()
            pastWeek = pastWeekResponse.json()

            # Finding mean price of item for the past week
            pastWeekDF = pd.json_normalize(pastWeek)
            itemName = pastWeekDF["itemName"][0]
            pastWeekDF = removeDailyItems(pastWeekDF)
            startingBidCol = pastWeekDF["startingBid"]
            pastWeekSD = startingBidCol.std()
            pastWeekMedian = startingBidCol.median()

            # Grabbing data for the 10 lowest BINs right now
            lowestBINsResponse = rq.get(lowestBINsURL, timeout=10)
            lowestBINsResponse.raise_for_status()
            lowestBINs = lowestBINsResponse.json()

            # Putting lowest BIN data into a Series
            lowestBINsDF = pd.json_normalize(lowestBINs)
            if (lowestBINsDF.empty):
                return
            lowestBINsCol = lowestBINsDF["startingBid"]

            # Buying if price dropped 5% from weekly median + 0.5 SD
            pastWeekBenchmark = pastWeekMedian + (0.5 * pastWeekSD)
            buyPrice = pastWeekBenchmark - (0.05 * pastWeekMedian)
            worthBuying = False
            print("-------",itemName,"-------")
            for price in lowestBINsCol:
                if (price <= buyPrice):
                    profitMargin = round((pastWeekBenchmark - price),0)
                    percentageDrop = 100 * round((profitMargin/pastWeekBenchmark),3)
                    print("Auction for",price,"is worth buying at -",percentageDrop,"%")
                    worthBuying = True

            if (not worthBuying):
                print(itemName,"is not worth buying right now.")
            print("The median price for",itemName,"was",int(pastWeekMedian),"coins over the past week.")
            print("The benchmark price for",itemName,"was",int(pastWeekBenchmark),"coins over the past week.")
            print()

            #plotWeek(pastWeekDF, lowestBINsDF, itemName)
        except rq.exceptions.RequestException as e:
            print("Error:", e)

def calculateTax(price):
    listingTax = 0
    match price:
        case x if x < 10000000:
            listingTax = price * 0.01
        case x if x >= 10000000 & x <= 99999999:
            listingTax = price * 0.02
        case _:
            listingTax = price * 0.025
    
    totalTax = listingTax + (price * 0.01)
    return totalTax

# Check whether it's worth selling investments
def checkInvestmentStatus(investments):
    investmentItems = list(investments.keys())
    for item in investmentItems:
        url = "https://sky.coflnet.com/api/auctions/tag/" + item + "/active/bin"
        response = rq.get(url, timeout = 10)
        response.raise_for_status
        report = response.json()

        df = pd.json_normalize(report)
        lowestBIN = df["startingBid"][0]
        tax = calculateTax(lowestBIN)
        for price in investments[item]:
            profitCoins = (lowestBIN - tax) - price
            profitPercentage = round((profitCoins / price),2) * 100
            if ((profitPercentage > 10.00) | (profitCoins > 9999999)):
                print(item,"at price",lowestBIN,"is worth selling | Bought for:",price,"| Profit:",profitCoins,"coins or ",profitPercentage,"%")
            else:
                print(item,"at price",lowestBIN,"is not worth selling | Bought for:",price,"| Profit:",profitCoins,"coins or",profitPercentage,"%")
            print()

itemTags = ["MITHRIL_DRILL_ENGINE", 
            "TITANIUM_DRILL_ENGINE", 
            "RUBY_POLISHED_DRILL_ENGINE", 
            "SAPPHIRE_POLISHED_DRILL_ENGINE", 
            "AMBER_POLISHED_DRILL_ENGINE", 
            "MITHRIL_FUEL_TANK",
            "TITANIUM_FUEL_TANK",
            "GEMSTONE_FUEL_TANK",
            "PERFECTLY_CUT_FUEL_TANK"]

#findPriceGaps(itemTags)

investments = {}
investments["AMBER_POLISHED_DRILL_ENGINE"] = [177499000, 180000000, 180000000]
investments["GEMSTONE_FUEL_TANK"] = [37499900, 38399999]
investments["PERFECTLY_CUT_FUEL_TANK"] = [79499000, 80000000, 80000000]

checkInvestmentStatus(investments)

# Next steps: 
# - have the program run on a regular basis
# - factor in tax when looking at benchmark price
# - rethink buy logic, could be getting APDE for 155m right now(???)
