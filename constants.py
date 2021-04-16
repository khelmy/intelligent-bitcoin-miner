from enum import Enum


# String values for machine names
# TODO: Add more machines
class MachineName(Enum):
    ANTMINER_S9 = 'Antminer S9'
    ANTMINER_S17 = 'Antminer S17'
    ANTMINER_T17 = 'Antminer T17'
    ANTMINER_S19 = 'Antminer S19'
    ANTMINER_T19 = 'Antminer T19'
    ANTMINER_S19_PRO = 'Antminer S19 Pro'

    MICROBT_M20S = 'MicroBT M20s'
    MICROBT_M21S = 'MicroBT M21s'
    MICROBT_M30S = 'MicroBT M30s'
    MICROBT_M31S = 'MicroBT M31s'

    INNOSILICON_T2T = 'Innosilicon T2T'


# Catalog of strategies
class Strategy(Enum):
    SELL_DAILY = "Sell Daily"
    LONG_BTC = "Long BTC"


# Enum for currencies
class Currency(Enum):
    BTC = 'BTC'
    USD = 'USD'
