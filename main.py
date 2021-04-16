import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
import numpy as np

from agents import *
from generators import *
from CMDataLoader import CMDataLoader
from Simulator import Simulator
from plotutils import update_layout_wrapper
import config
import constants
import random

# my_palette = ["#264653","#9D1DC8","#287271", "#645DAC","#636EFA", "#ECA400","#FE484E","#8484E8", "#03b800" ,"#9251e1","#F4A261"]
# my_palette = ["#54478c","#9D1DC8","#2c699a","#048ba8","#0db39e","#16db93","#83e377","#b9e769","#efea5a","#f1c453","#f29e4c"]
my_palette = ["#1f00a7","#9d1dc8","#00589f","#009b86","#00a367","#67a300","#645dac","#eca400","#fd7e00","#b6322b", "#FE484E"]
hardware_palette = ["#009b86", "#9D1DC8"]
opex_palette = ["#9D1DC8","#264653","#8484E8"]
primary_color = ["#9d1dc8"]


def save_csvs(prices, global_hash_rate, n_trials, user_positions, file_suffix):
    pd.DataFrame({'price': prices, 'hashrate': global_hash_rate, 'trials': n_trials}).to_csv(f"plots/{file_suffix}/env_values_{file_suffix}.csv", index = False)
    user_positions.to_csv(f"plots/{file_suffix}/user_values_{file_suffix}.csv", index = False)


def get_environment_plots(prices, global_hash_rate, n_trials, title_suffix):
    price_fig = update_layout_wrapper(px.line(x = list(range(len(prices))), y = prices,
                                              labels = {"y": "Price (USD)", "x": "Day"},
                                              title = f"Simulated Bitcoin Price over {n_trials} Trials {title_suffix}",
                                              color_discrete_sequence = primary_color,
                                              width=1600, height=900))
    hashrate_fig = update_layout_wrapper(px.line(x = list(range(len(global_hash_rate))), y = global_hash_rate,
                                                 labels = {"y": "Hash Rate (EH/s)", "x": "Day"},
                                                 title = f"Simulated Bitcoin Network Hash Rate over {n_trials} Trials {title_suffix}",
                                                 color_discrete_sequence = primary_color,
                                                 width=1600, height=900))

    return (price_fig, hashrate_fig)


def get_user_plots(user_positions, n_trials, title_suffix, elec_cost, palette):
    user_positions_e_c = user_positions.loc[user_positions.elec_cost == elec_cost]
    long_btc_fig = update_layout_wrapper(px.line(user_positions_e_c.loc[user_positions_e_c.strategy == constants.Strategy.LONG_BTC.value].sort_values(by=['day']),
                                                 x = "day", y = "total_position_usd", color = "machine_type",
                                                 labels = {"total_position_usd": "Simulated Position (USD)", "day": "Day", "machine_type": "Machine Type  "},
                                                 title = f"Simulated Position Value over {n_trials} Trials {title_suffix}, Long BTC, ${elec_cost} per kWh",
                                                 color_discrete_sequence = palette,
                                                 width=1600, height=900))
    sell_daily_fig = update_layout_wrapper(px.line(user_positions_e_c.loc[user_positions_e_c.strategy == constants.Strategy.SELL_DAILY.value].sort_values(by=['day']),
                                                   x = "day", y = "total_position_usd", color = "machine_type",
                                                   labels = {"total_position_usd": "Simulated Position (USD)", "day": "Day", "machine_type": "Machine Type  "},
                                                   title = f"Simulated Position Value over {n_trials} Trials {title_suffix}, Selling Daily, ${elec_cost} per kWh",
                                                   color_discrete_sequence = palette,
                                                   width=1600, height=900))
    return (long_btc_fig, sell_daily_fig)


def get_summary_plots(price_params, fee_params, block_subsidy, n_trials, title_suffix, file_suffix, user_machine_prices = config.machine_prices, elec_costs = [0.04, 0.07], palette = my_palette):
    init_prices = PriceGenerator(price_params).generate_prices()
    user_miners_long_btc, user_miners_sell_daily = UserMinerGenerator().generate_user_miners(machine_prices = user_machine_prices, elec_costs = elec_costs)
    env_miners = MinerGenerator().generate_miner_distribution()

    sim = Simulator(env_miners = env_miners,
                    user_miners_long_btc = user_miners_long_btc,
                    user_miners_sell_daily = user_miners_sell_daily,
                    prices = init_prices,
                    price_params = price_params,
                    fee_params = fee_params,
                    block_subsidy = block_subsidy)
    sim.run_simulation_n_trials(n_trials)

    user_positions = sim.get_avg_user_positions()
    prices = sim.get_avg_prices()
    global_hash_rate = sim.get_avg_global_hash_rate()

    price_fig, hashrate_fig = get_environment_plots(prices, global_hash_rate, n_trials, title_suffix)
    price_fig.write_image(f"plots/{file_suffix}/price_plot_{file_suffix}.png", scale=8)
    hashrate_fig.write_image(f"plots/{file_suffix}/hashrate_plot_{file_suffix}.png", scale=8)

    for elec_cost in user_positions.elec_cost.unique():
        user_figs = get_user_plots(user_positions, n_trials, title_suffix, elec_cost, palette)
        user_figs[0].write_image(f"plots/{file_suffix}/long_btc_plot_{file_suffix}_{int(elec_cost * 100)}.png", scale=8)
        user_figs[1].write_image(f"plots/{file_suffix}/sell_daily_plot_{file_suffix}_{int(elec_cost * 100)}.png", scale=8)
    save_csvs(prices, global_hash_rate, n_trials, user_positions, file_suffix)


def get_user_opex_plots(user_positions, n_trials, title_suffix, machine_type, palette):
    user_positions_m_t = user_positions.loc[user_positions.machine_type == machine_type.value]
    long_btc_fig = update_layout_wrapper(px.line(user_positions_m_t.loc[user_positions_m_t.strategy == constants.Strategy.LONG_BTC.value].sort_values(by=['day']),
                                                 x = "day", y = "total_position_usd", color = "elec_cost",
                                                 labels = {"total_position_usd": "Simulated Position (USD)", "day": "Day", "elec_cost": "Electricity Cost (USD/kWh)  "},
                                                 title = f"Simulated Position Value over {n_trials} Trials using {machine_type.value} {title_suffix}, Long BTC",
                                                 color_discrete_sequence = palette,
                                                 width=1600, height=900))
    sell_daily_fig = update_layout_wrapper(px.line(user_positions_m_t.loc[user_positions_m_t.strategy == constants.Strategy.SELL_DAILY.value].sort_values(by=['day']),
                                                   x = "day", y = "total_position_usd", color = "elec_cost",
                                                   labels = {"total_position_usd": "Simulated Position (USD)", "day": "Day", "elec_cost": "Electricity Cost (USD/kWh)  "},
                                                   title = f"Simulated Position Value over {n_trials} Trials using {machine_type.value} {title_suffix}, Selling Daily",
                                                   color_discrete_sequence = palette,
                                                   width=1600, height=900))
    return (long_btc_fig, sell_daily_fig)


def get_summary_plots_opex(price_params, fee_params, block_subsidy, n_trials, title_suffix, file_suffix, user_machine_prices = config.machine_prices, elec_costs = [0.04, 0.07], palette = opex_palette):
    init_prices = PriceGenerator(price_params).generate_prices()
    user_miners_long_btc, user_miners_sell_daily = UserMinerGenerator().generate_user_miners(machine_prices = user_machine_prices, elec_costs = elec_costs)
    env_miners = MinerGenerator().generate_miner_distribution()

    sim = Simulator(env_miners = env_miners,
                    user_miners_long_btc = user_miners_long_btc,
                    user_miners_sell_daily = user_miners_sell_daily,
                    prices = init_prices,
                    price_params = price_params,
                    fee_params = fee_params,
                    block_subsidy = block_subsidy)
    sim.run_simulation_n_trials(n_trials)

    user_positions = sim.get_avg_user_positions()
    prices = sim.get_avg_prices()
    global_hash_rate = sim.get_avg_global_hash_rate()

    price_fig, hashrate_fig = get_environment_plots(prices, global_hash_rate, n_trials, title_suffix)
    price_fig.write_image(f"plots/{file_suffix}/price_plot_{file_suffix}.png", scale=8)
    hashrate_fig.write_image(f"plots/{file_suffix}/hashrate_plot_{file_suffix}.png", scale=8)

    for machine_type in user_machine_prices:
        user_figs = get_user_opex_plots(user_positions, n_trials, title_suffix, machine_type, palette)
        user_figs[0].write_image(f"plots/{file_suffix}/long_btc_plot_{file_suffix}_{machine_type.value}.png", scale=8)
        user_figs[1].write_image(f"plots/{file_suffix}/sell_daily_plot_{file_suffix}_{machine_type.value}.png", scale=8)
    save_csvs(prices, global_hash_rate, n_trials, user_positions, file_suffix)


if __name__ == '__main__':
    random.seed(1032009)
    np.random.seed(1032009)
    n_trials = 25

    fee_params = CMDataLoader.get_historical_fee_params()
    block_subsidy = 6.25

    historical_price_params = CMDataLoader.get_historical_price_params()
    get_summary_plots(historical_price_params, fee_params, block_subsidy, n_trials, "with Historical Parameters", "historical")

    bearish_price_params = (historical_price_params[0], -1 * abs(historical_price_params[1]), historical_price_params[2])
    get_summary_plots(bearish_price_params, fee_params, block_subsidy, n_trials, "with Bearish Parameters", "bearish")

    corrections_price_params = (historical_price_params[0], 0, historical_price_params[2] * 1.25)
    get_summary_plots(corrections_price_params, fee_params, block_subsidy, n_trials, "in Bull Market with Corrections", "corrections")

    s9_s19_prices = {key: config.machine_prices[key] for key in [constants.MachineName.ANTMINER_S9, constants.MachineName.ANTMINER_S19]}
    get_summary_plots(historical_price_params, fee_params, block_subsidy, n_trials, "with Historical Parameters", "historical-machines", s9_s19_prices, [0.03], hardware_palette)

    get_summary_plots_opex(bearish_price_params, fee_params, block_subsidy, n_trials, "with Bearish Parameters", "bearish-opex", s9_s19_prices, [0.03, 0.04, 0.05], opex_palette)
