import multiprocessing
from copy import deepcopy
import numpy as np

from agents import *
from generators import *
from config import user_miner_specs
from constants import Currency, Strategy

from CMDataLoader import CMDataLoader


# Picklable wrapper for miner.update_positions
def update_positions(miner, price, block_reward, global_hash_rate):
    return miner.update_positions(price, block_reward, global_hash_rate)


# Picklable wrapper for run_simulation on new instance
def run_peer_simulation(env_miners, user_miners_long_btc, user_miners_sell_daily, prices, block_rewards, price_params, fee_params, block_subsidy):
    sim = Simulator(env_miners, user_miners_long_btc, user_miners_sell_daily, prices, block_rewards, price_params, fee_params, block_subsidy)
    return sim.run_simulation()


class Simulator():
    def __init__(self,
                 env_miners: list = MinerGenerator().generate_miner_distribution(),
                 user_miners_long_btc: Miner =  [Miner(machine_type = Machine.from_model(user_miner_specs['machine_name'].value),
                                                       strategy = Strategy.LONG_BTC,
                                                       elec_cost = user_miner_specs['elec_cost'],
                                                       n_machines = user_miner_specs['n_machines'],
                                                       is_scalable = False)],
                 user_miners_sell_daily: Miner =  [Miner(machine_type = Machine.from_model(user_miner_specs['machine_name'].value),
                                                         strategy = Strategy.SELL_DAILY,
                                                         elec_cost = user_miner_specs['elec_cost'],
                                                         n_machines = user_miner_specs['n_machines'],
                                                         is_scalable = False)],
                 # Non-peer pricing and block rewards
                 prices: list = PriceGenerator().generate_prices(),
                 block_rewards: list = BlockRewardGenerator().generate_block_rewards(),
                 # Parameters used for peer generation
                 price_params: tuple = CMDataLoader.get_historical_price_params(),
                 fee_params: tuple = CMDataLoader.get_historical_fee_params(),
                 block_subsidy: float = 6.25
                 ):
        self.miners = env_miners + user_miners_sell_daily + user_miners_long_btc
        self.prices = prices
        self.block_rewards = block_rewards

        self.global_hash_rate = [self.get_day_global_hash_rate()]

        # Store the other Simulators that have been initialized and run by this one
        self.peers = []

        self.user_long_btc_indexes = slice(len(self.miners) - len(user_miners_long_btc), len(self.miners))
        self.user_sell_daily_indexes = slice(-1 * (len(user_miners_long_btc) + len(user_miners_sell_daily)), -1 * len(user_miners_long_btc))
        self.env_indexes = slice(0, -1 * (len(user_miners_long_btc) + len(user_miners_sell_daily)))

        self.price_params = price_params
        self.fee_params = fee_params
        self.block_subsidy = block_subsidy

    def get_day_global_hash_rate(self):
        return sum([miner.get_hash_rate() for miner in self.miners])

    # For reporting single trials
    def __get_positions_internal(self, indexes):
        user_positions = list(map(lambda x: (x, x.get_positions()), self.miners[indexes]))
        user_pos_dfs = [user_df.assign(price = self.prices,
                                       global_hash_rate = self.global_hash_rate,
                                       global_mining_rev_btc = self.block_rewards,
                                       day = np.arange(len(self.prices)),
                                       machine_type = user_miner.machine_type.get_model(),
                                       machine_hash_rate = user_miner.machine_type.get_hash_rate(),
                                       machine_wattage = user_miner.machine_type.get_wattage_kw(),
                                       n_machines = user_miner.n_machines,
                                       strategy = user_miner.strategy.value,
                                       elec_cost = user_miner.elec_cost)
                               .assign(user_hash_rate = lambda x: x.machine_hash_rate * x.n_machines,
                                       revenue_btc = lambda x: x.global_mining_rev_btc * x.machine_hash_rate * x.n_machines / x.global_hash_rate,
                                       expense_usd = lambda x: x.machine_wattage * x.n_machines * x.elec_cost * 24)
                               .assign(total_position_usd = lambda x: x[Currency.USD.value] + (x[Currency.BTC.value] * x.price))
                        for (user_miner, user_df) in user_positions]
        all_positions = pd.concat(user_pos_dfs, ignore_index = True)
        return all_positions

    def get_user_positions_long_btc(self):
        return self.__get_positions_internal(self.user_long_btc_indexes)

    def get_user_positions_sell_daily(self):
        return self.__get_positions_internal(self.user_sell_daily_indexes)

    def get_user_positions(self):
        return self.get_user_positions_long_btc().append(self.get_user_positions_sell_daily(), ignore_index = True)

    # For running single trial
    def run_simulation(self):
        pool = multiprocessing.Pool()
        for i in range(1, len(self.prices)):
            self.miners = pool.starmap(update_positions, [(miner, self.prices[i], self.block_rewards[i], self.global_hash_rate[-1]) for miner in self.miners])
            self.global_hash_rate += [self.get_day_global_hash_rate()]
        return self

    # For running multiple trials
    def run_simulation_n_trials(self, n_trials = 2):
        pool = multiprocessing.pool.ThreadPool()
        miners_copy = deepcopy(self.miners)

        args = [(miners_copy[self.env_indexes], miners_copy[self.user_long_btc_indexes], miners_copy[self.user_sell_daily_indexes],
                 PriceGenerator(price_params = self.price_params).generate_prices(n_days = len(self.prices) - 1),
                 BlockRewardGenerator().generate_block_rewards(fee_params = self.fee_params,
                                                               block_subsidy = self.block_subsidy,
                                                               n_days = len(self.block_rewards) - 1),
                 self.price_params, self.fee_params, self.block_subsidy) for i in range(n_trials)]
        self.peers = pool.starmap(run_peer_simulation, args)
        return self.peers


    def get_avg_prices(self):
        peer_prices = [peer.prices for peer in self.peers]
        avg_prices = [sum([peer.prices[i] for peer in self.peers]) / len(self.peers) for i in range(len(self.peers[0].prices))]
        return avg_prices

    def get_avg_global_hash_rate(self):
        peer_hash_rates = [peer.global_hash_rate for peer in self.peers]
        avg_global_hash_rate = [sum([peer.global_hash_rate[i] for peer in self.peers]) / len(self.peers) for i in range(len(self.peers[0].global_hash_rate))]
        return avg_global_hash_rate


    def get_avg_user_positions(self):
        peer_user_positions = [peer.get_user_positions() for peer in self.peers]
        return pd.concat(peer_user_positions, ignore_index=True).groupby(['strategy', 'machine_type', 'elec_cost', 'day', 'n_machines']).mean().reset_index(level=['strategy', 'machine_type', 'elec_cost', 'day', 'n_machines'])
