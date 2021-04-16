from enum import Enum
from functools import lru_cache
import pandas as pd

import config
from constants import *
from CMDataLoader import CMDataLoader


# Specs of a single machine
class MachineInstance():
    def __init__(self,
                 model: str,
                 hash_rate: int,
                 wattage: float,
                 btc_price_0: float = CMDataLoader.get_historical_price_params()[0],
                 global_hash_rate_0: float = CMDataLoader.get_historical_hash_rate().iloc[-1]
                 ):
        # Machine specs
        self.model = model.value
        self.hash_rate = hash_rate # TH/s
        self.wattage = wattage # power consumption, in watts

        # Model variables
        self.machine_price_0 = config.machine_prices[model] # USD price of machine
        self.growth_factor = config.machine_growth_factors[model] # growth factor (see docs)
        self.setup_time = config.machine_setup_times[model] # delay in upscaling machine, in days

        # External variables
        self.btc_price_0 = btc_price_0
        self.global_hash_rate_0 = global_hash_rate_0

    def get_model(self):
        return self.model

    def get_hash_rate(self):
        return self.hash_rate

    @lru_cache
    def get_wattage_kw(self):
        return self.wattage / 1_000

    @lru_cache
    def get_machine_price(self, btc_price_n, global_hash_rate_n):
        return self.machine_price_0 * (btc_price_n * self.global_hash_rate_0) / (self.btc_price_0 * global_hash_rate_n)

    def get_growth_factor(self):
        return self.growth_factor

    def get_setup_time(self):
        return self.setup_time

    def __repr__(self):
        return f"MachineInstance({self.model})"


# Catalog of machine types
# TODO: Add more machines
# TODO: Find more convincing growth factor estimation
# TODO: Add dynamic machine prices
class Machine(Enum):
    ANTMINER_S9 = MachineInstance(MachineName.ANTMINER_S9, 14.5, 1350)
    ANTMINER_S17 = MachineInstance(MachineName.ANTMINER_S17, 56, 2520)
    ANTMINER_T17 = MachineInstance(MachineName.ANTMINER_T17, 40, 2200)
    ANTMINER_S19 = MachineInstance(MachineName.ANTMINER_S19, 95, 3250)
    ANTMINER_T19 = MachineInstance(MachineName.ANTMINER_T19, 84, 3150)
    ANTMINER_S19_PRO = MachineInstance(MachineName.ANTMINER_S19_PRO, 110, 3250)

    MICROBT_M20S = MachineInstance(MachineName.MICROBT_M20S, 68, 3360)
    MICROBT_M21S = MachineInstance(MachineName.MICROBT_M21S, 56, 3360)
    MICROBT_M30S = MachineInstance(MachineName.MICROBT_M30S, 86, 3268)
    MICROBT_M31S = MachineInstance(MachineName.MICROBT_M31S, 70, 3220)

    INNOSILICON_T2T = MachineInstance(MachineName.INNOSILICON_T2T, 24, 1980)

    @classmethod
    def from_model(cls, model: str):
        return [m for m in cls if m.value.get_model() == model][0]


# Miner equivalence class: aggregate all miners of same machine type, strategy, electricity cost
class Miner():
    def __init__(self,
                 machine_type: MachineInstance = Machine.MICROBT_M31S,
                 strategy: str = Strategy.SELL_DAILY,
                 lag: int = 30,
                 elec_cost: float = 0.04,
                 n_machines: int = 1000,
                 historical_global_mining_rev_usd: pd.Series = CMDataLoader.get_historical_miner_revenue_usd(),
                 historical_hash_rate: pd.Series = CMDataLoader.get_historical_hash_rate(),
                 is_scalable: bool = True
                 ):
        self.machine_type = machine_type.value
        self.strategy = strategy
        self.n_machines = n_machines
        self.elec_cost = elec_cost
        self.lag = lag

        # User's miner is the only one that isn't scalable
        self.is_scalable = is_scalable

        # Seed historical pnl
        self.pnl_usd = list(self.__calc_pnl_usd(historical_global_mining_rev_usd, historical_hash_rate))

        self.position_changes = pd.DataFrame({Currency.BTC.value: [0], Currency.USD.value: [0]})

        self.days_active = 0
        # Stores days_active: delivered machines
        self.pending_setups = dict()
        # Number of machines currently pending
        self.pending_count = 0

    # Used to scale operation before simulation starts to line up with current hashrate
    def scale_operation_scalar(self, scalar):
        self.n_machines = int(self.n_machines * scalar)

    def __calc_expense_usd(self):
        return self.machine_type.get_wattage_kw() * self.n_machines * self.elec_cost * 24

    # How much profit is earned in a day, if the machines are on?
    def __calc_pnl_usd(self, global_mining_rev_usd, global_hash_rate):
        revenue = global_mining_rev_usd * (self.machine_type.get_hash_rate() * self.n_machines) / global_hash_rate
        expense = self.__calc_expense_usd()
        return revenue - expense

    # How much profit is earned in a day?
    # Adjusts for lag. Machines scale up/down according to lagged profits
    def __calc_usd_profit(self, global_mining_rev_usd, global_hash_rate):
        self.pnl_usd += [self.__calc_pnl_usd(global_mining_rev_usd, global_hash_rate)]
        return self.pnl_usd[-1]

    def __scale_down_operation(self, pnl_lagged):
        machine_reduction = pnl_lagged // (self.__calc_expense_usd() / self.n_machines)
        self.n_machines = max(0, self.n_machines - abs(machine_reduction))

    # Hook up machines that have already waited out the setup time
    def __scale_up_pending(self):
        if self.days_active in self.pending_setups:
            self.n_machines += self.pending_setups[self.days_active]
            self.pending_count -= self.pending_setups[self.days_active]

    # Place orders to scale up operation (subject setup time delay)
    def __scale_up_operation(self, pnl_lagged, price_btc_usd, global_hash_rate):
        machine_addition_raw = self.machine_type.get_growth_factor() * (pnl_lagged - self.__calc_expense_usd()) // self.machine_type.get_machine_price(price_btc_usd, global_hash_rate)
        machine_addition = max(abs(machine_addition_raw) - self.pending_count, 0)

        pending_setup_day = self.days_active + self.machine_type.get_setup_time()
        self.pending_setups[pending_setup_day] = machine_addition
        self.pending_count += machine_addition

    # Scales miner operations according to scaling formula
    def __scale_operation(self, price_btc_usd, global_hash_rate):
        self.__scale_up_pending()
        if len(self.pnl_usd) >= self.lag:
            pnl_lagged = sum(self.pnl_usd[-self.lag:])
            if pnl_lagged < 0 and self.n_machines > 0:
                self.__scale_down_operation(pnl_lagged)
            elif pnl_lagged > self.__calc_expense_usd():
                self.__scale_up_operation(pnl_lagged, price_btc_usd, global_hash_rate)

    @staticmethod
    def __calc_sell_daily_position_change(usd_profit, price_btc_usd):
        return {Currency.BTC.value: 0, Currency.USD.value: usd_profit}

    @staticmethod
    def __calc_long_btc_position_change(usd_profit, price_btc_usd):
        return {Currency.BTC.value: usd_profit / price_btc_usd, Currency.USD.value: 0}

    def __calc_position_changes(self, price_btc_usd, global_mining_rev_btc, global_hash_rate):
        usd_profit = self.__calc_usd_profit(price_btc_usd * global_mining_rev_btc, global_hash_rate)
        if self.is_scalable:
            self.__scale_operation(price_btc_usd, global_hash_rate)
        if self.strategy == Strategy.SELL_DAILY:
            return self.__calc_sell_daily_position_change(usd_profit, price_btc_usd)
        # If LONG_BTC
        return self.__calc_long_btc_position_change(usd_profit, price_btc_usd)

    def update_positions(self, price_btc_usd, global_mining_rev_btc, global_hash_rate):
        daily_position_changes = self.__calc_position_changes(price_btc_usd, global_mining_rev_btc, global_hash_rate)
        self.days_active += 1

        self.position_changes = self.position_changes.append({
                                                              Currency.BTC.value: daily_position_changes[Currency.BTC.value],
                                                              Currency.USD.value: daily_position_changes[Currency.USD.value]
                                                              }, ignore_index = True)
        return self

    def get_hash_rate(self):
        return self.machine_type.get_hash_rate() * self.n_machines

    def get_elec_cost(self):
        return self.elec_cost

    def get_positions(self):
        return self.position_changes.cumsum()

    def __repr__(self):
        return f"Miner({self.machine_type}, {self.strategy}, {self.n_machines}, {self.elec_cost})"

    def get_params():
        return (self.machine_type, self.strategy, self.n_machines, self.elec_cost, self.lag)
