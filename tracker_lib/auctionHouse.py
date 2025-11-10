import matplotlib.pyplot as plt
import requests as rq
import pandas as pd
from datetime import datetime as dt, timedelta as td
import time
"""
Parameters: URL to use as API endpoint

Function: GETs data from the endpoint, turns it into a Dataframe

Returns: auction house data (pandas Dataframe)
"""
def getItemData(url):
    response = rq.get(url, timeout = 10)
    response.raise_for_status()
    report = response.json()
    dataframe = pd.json_normalize(report)
    
    return dataframe
"""
Parameters: past week auctions data (pandas Dataframe)

Function: removes extreme values of starting bid, used only when plotting the BIN data

Returns: None
"""
def cleanData(dataframe):
    averagePrice = dataframe["startingBid"].mean()
    standardDeviation = dataframe["startingBid"].std()
    low = averagePrice - (5 * standardDeviation)
    high = averagePrice + (5 * standardDeviation)
    return dataframe[dataframe["startingBid"].between(low,high)]

"""
Parameters: item tag as it appears in Hypixel's backend (String)

Function: creates a scatter plot for the past week of BIN auctions sold

Returns: None
"""
def plotData(itemTag):
    pastWeekURL = "https://sky.coflnet.com/api/auctions/tag/" + itemTag + "/sold"
    lowestBINsURL = "https://sky.coflnet.com/api/auctions/tag/" + itemTag + "/active/bin"

    pastWeekDF = getItemData(pastWeekURL)
    lowestBINsDF = getItemData(lowestBINsURL)

    pastWeekDF = cleanData(pastWeekDF)
    medianPrice = pastWeekDF["startingBid"].median()

    pastWeekDF["start"] = pd.to_datetime(pastWeekDF["start"], format = "%Y-%m-%dT%H:%M:%S", errors = "coerce")
    pastWeekDF = pastWeekDF.dropna(subset=["start", "startingBid"])
    pastWeekDF = pastWeekDF.sort_values("start")

    plt.figure(figsize=(15,10))
    title = "Weekly History & Median for " + pastWeekDF["itemName"][0]
    plt.title(title)
    plt.ylabel("Price")
    plt.xlabel("Date")

    plt.scatter(pastWeekDF["start"], pastWeekDF["startingBid"], color = "red", s = 5)
    plt.ticklabel_format(style="plain", axis="y")
    plt.scatter(lowestBINsDF["start"], lowestBINsDF["startingBid"], color = "green", s = 7.5)
    plt.axhline(y = medianPrice, color = "blue", linestyle = "--")
    plt.show()

"""
Parameters: past week auctions data (pandas DataFrame)

Function: remove any BINs purchased in the past 24 hours (don't want any recent changes to affect median/standard deviation of the data from the past week as a whole)

Returns: past week of BINs without the last 24 hours (pandas Dataframe)
"""
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

"""
Parameters: all the item tags to check (List), whether this is a test (Boolean, defaults to False)

Function: 
- Regular Circumstances: finds items that have dipped in price (15% below their weekly benchmark values) and prints them
- Test: goes through all items that appear on the auction house and determine whether it's a good idea to track it, based on median price and volume. I only needed this once but I figured I'd keep the code here since I spent a while on it 

Returns:
- Test: all items with sufficient price and volume to be worth tracking
"""
def findPriceGaps(itemTags, test = False):
    
    bestItemsList = []
    for item in itemTags:
        # Don't want to overwhelm their API servers with 5000+ requests
        time.sleep(0.5)
        
        pastWeekURL = "https://sky.coflnet.com/api/auctions/tag/" + item + "/sold"
        lowestBINsURL = "https://sky.coflnet.com/api/auctions/tag/" + item + "/active/bin"

        try:
            # Create dataframes for past week data, current lowest BIN data
            pastWeekDF = getItemData(pastWeekURL)
            lowestBINsDF = getItemData(lowestBINsURL)
            
            # Skipping any items with incorrect tags
            if pastWeekDF.empty or "itemName" not in pastWeekDF.columns:
                print(f"Skipping invalid or empty tag: {item}")
                continue
            
            # Grabbing information like item name, mean, standard deviation
            itemName = pastWeekDF["itemName"][0]
            pastWeekDF = removeDailyItems(pastWeekDF)
            startingBidCol = pastWeekDF["startingBid"]
            pastWeekSD = startingBidCol.std()
            pastWeekMedian = startingBidCol.median()

            # Putting lowest BIN data into a Series containing just price
            if (lowestBINsDF.empty):
                continue
            lowestBINsCol = lowestBINsDF["startingBid"]

            # Normal price check (not looking for best items)
            if not test:
                # Buying if price dropped 15% from weekly median + 0.5 SD, factoring in taxes
                pastWeekBenchmark = pastWeekMedian + (0.5 * pastWeekSD)
                buyPrice = pastWeekBenchmark - (0.15 * pastWeekBenchmark + calculateTax(pastWeekBenchmark))
                worthBuying = False
                for price in lowestBINsCol:
                    if ((price <= buyPrice) or (pastWeekBenchmark - price >= 19999999)):
                        if (not worthBuying):
                            print("-------",itemName,"-------")
                        profitMargin = round((pastWeekBenchmark - price - calculateTax(price)),0)
                        percentageDrop = 100 * round(((profitMargin - calculateTax(price))/pastWeekBenchmark),3)
                        print("Auction for",price,"is worth buying at -",percentageDrop,"%")
                        worthBuying = True

                if (not worthBuying):
                    continue
                print("The median price for",itemName,"was",int(pastWeekMedian),"coins over the past week.")
                print("The benchmark price for",itemName,"was",int(pastWeekBenchmark),"coins over the past week. \n")

                plot = (input("Would you like to plot the data for " + item + "? Y/N \n") == "Y")

                if (plot):
                    plotData(item)
                    quit = (input("Would you like to move on to the next item? Y/N: \n") == "N")
                    if (quit):
                        break
            
            # Looking for best items (>8,000,000 coins, >25 sales/day)
            else:
                pastWeekBINs = pastWeekDF["startingBid"]
                if (pastWeekBINs.max() == 0):
                    continue
                pastWeekVolume = len(pastWeekBINs) / 7
                print(item + ":")
                print("Median: " + str(pastWeekMedian))
                print("Volume: " + str(pastWeekVolume))
                if ((pastWeekMedian >= 8000000) & (pastWeekVolume >= 25)):
                    bestItemsList.append(item)
                    print("Added " + item + " to best items list")
        except rq.exceptions.RequestException as e:
            print("Error:", e)
    # Only return items if it's findBestItems()
    if (test):
        return bestItemsList

"""
Parameters: price of the BIN (integer)

Function: calculate tax for the BIN price, with different brackets based on the listing price and a claim tax added at the end. The numbers are defined by Hypixel.

Returns: the tax that would be spent auctioning off the item (integer)
"""  
def calculateTax(price):
    listingTax = 0
    match price:
        case x if x < 10000000:
            listingTax = price * 0.01
        case x if (x >= 10000000) & (x <= 99999999):
            listingTax = price * 0.02
        case _:
            listingTax = price * 0.025
    
    totalTax = listingTax + (price * 0.01)
    return totalTax

"""
Parameters: items in which the user is currently invested (Dictionary)

Function: checks if item price has increased 10% or if profit is >= 10m coins, factoring in tax, or if there are none of the item on the Auction House. Prints the result.

Returns: None
"""
def checkInvestmentStatus(investments):
    if (not investments):
        return
    investmentItems = list(investments.keys())
    totalInvested = 0
    for item in investmentItems:
        url = "https://sky.coflnet.com/api/auctions/tag/" + item + "/active/bin"
        response = rq.get(url, timeout = 10)
        response.raise_for_status
        report = response.json()

        dataframe = pd.json_normalize(report)
        if (dataframe.empty):
            print("There are NO " + item + " on the auction house!")
            print()
            continue
        lowestBIN = dataframe["startingBid"][0]
        tax = calculateTax(lowestBIN)
        for price in investments[item]:
            totalInvested += price
            profitCoins = (lowestBIN - tax) - price
            profitPercentage = round((profitCoins / price),2) * 100
            if ((profitPercentage >= 10.00) | (profitCoins > 9999999)):
                print(item,"at price",lowestBIN,"is worth selling | Bought for:",price,"| Profit:",profitCoins,"coins or ",profitPercentage,"% \n")
            else:
                print(item,"at price",lowestBIN,"is NOT worth selling | Bought for:",price,"| Profit:",profitCoins,"coins or",profitPercentage,"% \n")

    print(f"Total Current Investment: {totalInvested:,}")

"""
Parameters: None

Function: filter from all item tags to only items sold on the auction that actually exist to save time when parsing all the items (goes from like 7500 to 2500). Then uses findPriceGaps() to actually parse the items, since that code can be reused for this purpose. Prints the resulting list.

Returns: None
"""
def findBestItems():
    url = "https://sky.coflnet.com/api/items"
    response = rq.get(url, timeout = 10)
    response.raise_for_status
    report = response.json()

    itemsDF = pd.json_normalize(report)

    # Getting rid of a bunch of tags that don't exist, apparently, to save time when parsing all items
    auctionItemTagsDF = itemsDF[
    (itemsDF["flags"] == "AUCTION") &
    (~itemsDF["tag"].str.startswith(("PET", "RUNE", "POTION"))) &
    (~itemsDF["tag"].str.contains(":")) &
    (~itemsDF["tag"].str.contains(r"\d{1,2}$"))
    ]
    itemTags = list(auctionItemTagsDF["tag"])
    print(len(itemTags))

    bestItems = findPriceGaps(itemTags, test = True)
    print(bestItems)


# Next steps: 
# - Plot a 2-day moving average and leave the rest as a scatterplot
# - Revisit buy logic and see if the standard deviation stuff is a good idea (it wasn't for the bazaar version)
# - Start looking at risk metrics
