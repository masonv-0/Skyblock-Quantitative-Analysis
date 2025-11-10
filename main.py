import sys
import tracker_lib.bazaar as bz
import tracker_lib.auctionHouse as ah

# ------- Credit to https://sky.coflnet.com/api for all API endpoints and data ------- # 

# ------- Sample Information ------- #

# Auction House:
targetAuctionItems = ['CANDY_RELIC', 'BITS_TALISMAN', 'CATACOMBS_EXPERT_RING', 'TREASURE_RING', 'BEASTMASTER_CREST_LEGENDARY', 'RAZOR_SHARP_SHARK_TOOTH_NECKLACE', 'MINOS_RELIC', 'SPIDER_ARTIFACT', 'RED_CLAW_ARTIFACT', 'OVERFLUX_POWER_ORB', 'JERRY_TALISMAN_BLUE', 'MITHRIL_FUEL_TANK', 'MITHRIL_DRILL_ENGINE', 'TITANIUM_DRILL_ENGINE', 'TITANIUM_RELIC', 'TITANIUM_FUEL_TANK', 'WARDEN_HEART', 'SHARD_OF_THE_SHREDDED', 'ETHERWARP_CONDUIT', 'JUDGEMENT_CORE', 'GEMSTONE_FUEL_TANK', 'GOBLIN_OMELETTE_SPICY', 'PERFECTLY_CUT_FUEL_TANK', 'GOBLIN_OMELETTE_BLUE_CHEESE', 'BURNING_KUUDRA_CORE', 'EVERBURNING_FLAME', 'HIGH_CLASS_ARCHFIEND_DICE', 'POCKET_SACK_IN_A_SACK', 'VACCINE_ARTIFACT', 'TRAPPER_CREST', 'GOLD_GIFT_TALISMAN', 'FERMENTO_ARTIFACT', 'VAMPIRE_DENTIST_RELIC', 'INTIMIDATION_RELIC', 'INFINI_VACUUM_HOOVERIUS', 'STORM_IN_A_BOTTLE', 'POSTCARD', 'CENTURY_RING', 'SEAL_RING', 'HOTSPOT_HOOK', 'MEDIUM_FISHING_NET', 'TURBO_FISHING_NET', 'PRESSURE_ARTIFACT', 'SHRIVELED_WASP', 'PRIMORDIAL_EYE', 'DYE_MARINE', 'DYE_SPOOKY', 'NECRON_HANDLE', 'RUBY_POLISHED_DRILL_ENGINE', 'SAPPHIRE_POLISHED_DRILL_ENGINE', 'AMBER_POLISHED_DRILL_ENGINE']

auctionInvestments = {}
auctionInvestments["JERRY_TALISMAN_BLUE"] = [10500000]
auctionInvestments["GOBLIN_OMELETTE_BLUE_CHEESE"] = [113799999, 114000000]
auctionInvestments["PRIMORDIAL_EYE"] = [134900000]
auctionInvestments["GOBLIN_OMELETTE_SPICY"] = [13000000, 13000000]
auctionInvestments["STORM_IN_A_BOTTLE"] = [10999999, 11000000, 11000000]
auctionInvestments["TURBO_FISHING_NET"] = [34000000]
auctionInvestments["GEMSTONE_FUEL_TANK"] = [36000000]
auctionInvestments["PRESSURE_ARTIFACT"] = [8390000]

# Bazaar:
targetBazaarItems = [
    "FUMING_POTATO_BOOK",
    "RECOMBOBULATOR_3000",
    "DRAGON_HORN",
    "DRAGON_CLAW",
    "SUPERIOR_FRAGMENT",
    "SHADOW_WARP_SCROLL",
    "GIANT_FRAGMENT_DIAMOND",
    "WITHER_BLOOD",
    "PRECURSOR_GEAR",
    "COLOSSAL_EXP_BOTTLE",
    "FIRST_MASTER_STAR",
    "SECOND_MASTER_STAR",
    "THIRD_MASTER_STAR",
    "FOURTH_MASTER_STAR",
    "FIFTH_MASTER_STAR"
]

# [Price, Quantity]
bazaarInvestments = {}
bazaarInvestments["SHADOW_WARP_SCROLL"] = [200000000, 1]
bazaarInvestments["SECOND_MASTER_STAR"] = [18542693, 4]

# ------- User Input ------- #

# User chooses Auction House or Bazaar tracker
answer = int(input("Which market would you like to analyze? \n" \
"|1| Auction House \n" \
"|2| Bazaar \n"))
print()

auctionInput = 0
bazaarInput = 0

# User chooses what to do in chosen tracker
match answer:
    case 1:
        auctionInput = int(input("What would you like to do? \n"
                        "|1| Check Target Items \n"
                        "|2| Check Investment Status \n"
                        "|3| Find Best Items \n"
                        "|4| Graph Item History \n"))
        print()
    case 2:
        bazaarInput = int(input("What would you like to do? \n"
                    "|1| Check Target Flips (buy/sell order) \n"
                    "|2| Check Investment Status \n"  
                    "|3| Find Best Items \n"
                    "|4| Check Strategy History \n" \
                    "|5| Graph Item History \n"))
        print()
    case _:
        print("Invalid input!")
        sys.exit(0)

# Auction House methods
match auctionInput:
    case 0:
        pass
    case 1:
        ah.findPriceGaps(targetAuctionItems)
    case 2:
        ah.checkInvestmentStatus(auctionInvestments)
    case 3:
        #findBestItems()
        print("Best items have already been found")
    case 4:
        item = input("Please enter the item tag: \n")
        ah.plotData(item)
    case _:
        print("Invalid input!")
        sys.exit(0)

# Bazaar methods
match bazaarInput:
    case 0:
        pass
    case 1:
        bz.analyzePrice(targetBazaarItems)
    case 2:
        bz.checkInvestmentStatus(bazaarInvestments)
    case 3:
        #bz.sortAllItems()
        print("Items have already been sorted")
    case 4:
        totalProfitList, totalInvestedList = bz.checkStrategyHistory(targetBazaarItems)
        totalProfit = sum(totalProfitList)
        totalInvested = sum(totalInvestedList)
        print(f"Total Profit for all items: {totalProfit:.2f}")
        print(f"Total Invested for all items: {totalInvested:.2f}")
        print(f"Total ROI for all items: {(totalProfit/totalInvested):.2f}")
    case 5:
        item = input("Please enter the item tag: \n")
        bz.plotData(item)
    case _:
        print("Invalid input!")
        sys.exit(0)