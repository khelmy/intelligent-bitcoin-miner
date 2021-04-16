import numpy as np

import config
from agents import *
from constants import *
from CMDataLoader import CMDataLoader


# Generates Bitcoin prices
# Note: log-transformed linear-regression-fit historical price params should be directly convertible
class PriceGenerator():
    def __init__(self,
                 price_params: tuple = CMDataLoader.get_historical_price_params()
                 ):
        self.start_price, self.drift, self.std_dev = price_params

    # Uses geometric brownian motion to generate price values
    def generate_prices(self, n_days=100):
        prices = np.ones(n_days + 1) * self.start_price
        for i in range(1, n_days + 1):
            noise = np.random.normal()
            prices[i] = prices[i-1] * (1 + self.drift + self.std_dev * noise)
        return list(prices)


# Generates BTC-denominated daily block rewards
# Uses lognormal distribution
class BlockRewardGenerator():
    # Mean, sigma are mean and sigma of normal distribution, not log-normal distribution
    # This is compatible with both numpy and how we break down the data
    def generate_block_rewards(self,
                               fee_params: tuple = CMDataLoader.get_historical_fee_params(),
                               block_subsidy: float = 6.25,
                               n_days: int = 100
                               ):
        fee_mean, fee_sigma = fee_params
        return list((block_subsidy + np.random.lognormal(fee_mean, fee_sigma, n_days + 1)) * 6 * 24)


# Generates distribution of miners
class MinerGenerator():
    def __init__(self,
                 lag: int = 30,
                 # Dict mapping electricity price to proportion
                 elec_cost_props: dict = config.elec_cost_props,
                 # Dict mapping strategy to proportion
                 strategy_props: dict = config.strategy_props
                 ):
        self.lag = lag
        self.elec_cost_props = elec_cost_props
        self.strategy_props = strategy_props

    def __generate_miner_elec_distribution(self,
                                           machine_type: MachineInstance = Machine.MICROBT_M31S,
                                           strategy: str = Strategy.SELL_DAILY,
                                           n_machines_total: int = 100):
        return [Miner(machine_type, strategy, self.lag, elec_cost, n_machines_total * self.elec_cost_props[elec_cost] * self.strategy_props[strategy])
                for elec_cost in self.elec_cost_props]

    def __generate_miner_distribution_unscaled(self,
                                               # Dict mapping model to proportion
                                               machine_counts: dict
                                               ):
        miners_nested = [self.__generate_miner_elec_distribution(Machine.from_model(machine_name.value), strategy, machine_counts[machine_name])
                         for machine_name in MachineName
                         for strategy in Strategy]
        miners = [miner for miner_tranche in miners_nested for miner in miner_tranche]
        return miners

    def __scale_miner_distribution(self, miners: list, starting_hashrate: float):
        def get_simulated_hash_rate(miners):
            return sum([miner.get_hash_rate() for miner in miners])

        hashrate_scalar = starting_hashrate / get_simulated_hash_rate(miners)
        for miner in miners:
            miner.scale_operation_scalar(hashrate_scalar)
        return miners

    def generate_miner_distribution(self,
                                    # Dict mapping model to proportion
                                    machine_counts_unscaled: dict = config.machine_counts,
                                    starting_hashrate: float = CMDataLoader.get_historical_hash_rate().dropna().iloc[-1]
                                    ):
        miners_unscaled = self.__generate_miner_distribution_unscaled(machine_counts_unscaled)
        miners = self.__scale_miner_distribution(miners_unscaled, starting_hashrate)
        return miners


class UserMinerGenerator():
    @staticmethod
    def generate_user_miners(budget: int = 1_000_000,
                             machine_prices: dict = config.machine_prices,
                             elec_costs: list = [0.04, 0.07]
                             ):
        user_miners_long_btc = [Miner(machine_type = Machine.from_model(machine_type.value),
                                      strategy = Strategy.LONG_BTC,
                                      elec_cost = elec_cost,
                                      n_machines = budget // machine_prices[machine_type],
                                      is_scalable = False)
                                for elec_cost in elec_costs
                                for machine_type in machine_prices]
        user_miners_sell_daily = [Miner(machine_type = Machine.from_model(machine_type.value),
                                       strategy = Strategy.SELL_DAILY,
                                       elec_cost = elec_cost,
                                       n_machines = budget // machine_prices[machine_type],
                                       is_scalable = False)
                                 for elec_cost in elec_costs
                                 for machine_type in machine_prices]
        return (user_miners_long_btc, user_miners_sell_daily)
