# Skyblock Quantitative Analysis

## Overview
This project is the start of my exploration of quantitative finance, an interest which was sparked by TigerQuant, a club at Mizzou that focuses on the intersection of computer science and finance. I took some of the big picture ideas we talked about and applied them to the economy of a videogame I used to play a lot: Hypixel Skyblock. 

---

## API
Coflnet, a third-party group, has public API endpoints to access data about current and historic prices on both the Auction House and Bazaar. This is the backbone of my strategies and I'm very thankful to sky.coflnet.com for allowing access to this information.

---

## Auction House
Skyblock's auction house allows players to buy and sell major items, with most traffic coming in the form of Buy It Now bids (BINs). Prices for these items vary based on supply and demand, which means there are gaps to exploit. The module I wrote for this market targets items that are expensive and have high volume. It works by comparing the current price of an item to its price over the past week, and recommending when to buy based on the difference. I also have a system in place for me to store data on items I bought, so that it can check every so often whether they’re worth selling.

---

## Bazaar
The Bazaar is a lot closer to the stock market, with bids/asks on commodities and a spread between them. The one difference is that inflation on the Bazaar is minimal, usually only happening in response to major game updates. Prices still fluctuate pretty substantially over time, though, which makes investment possible. The module I wrote for this market works in a similar way to the Auction House, although I had to be a bit more specific when finding target items, which I did by making sure the bid/ask spread wasn’t too large. The strategy for the Bazaar is a bit more fleshed out, but works the same way as the Auction House: buy when items dip, log them, sell when they go back up.

---

## Spreadsheet
I track my strategies and results in the spreadsheet linked below:  
[Google Sheets Link](https://docs.google.com/spreadsheets/d/1_NEwompAn--ddyDnFmIr-Q5OspMyXZZycSmzeZMzGQw/edit?usp=sharing)
