from constants import MachineName, Strategy

user_miner_specs = {
    'machine_name': MachineName.ANTMINER_S9,
    'elec_cost': 0.04,
    'n_machines': 1000,
}

# Layers should be user-adjustable
# Default: 5% $0.02, 10% $0.03, 20% $0.04, 35% $0.05, 20% $0.06, 5% $0.07, 5% $0.08
# Dict mapping electricity price to proportion
elec_cost_props = {
    0.02: 0.05,
    0.03: 0.10,
    0.04: 0.20,
    0.05: 0.35,
    0.06: 0.20,
    0.07: 0.05,
    0.08: 0.05
}

# Machine Model Variables
# Starting counts of each machine (unscaled)
machine_counts = {
    MachineName.ANTMINER_S9: 3_000_000,
    MachineName.ANTMINER_S17: 300_000,
    MachineName.ANTMINER_T17: 350_000,
    MachineName.ANTMINER_S19: 80_000,
    MachineName.ANTMINER_T19: 50_000,
    MachineName.ANTMINER_S19_PRO: 80_000,

    MachineName.MICROBT_M20S: 400_000,
    MachineName.MICROBT_M21S: 250_000,
    MachineName.MICROBT_M30S: 120_000,
    MachineName.MICROBT_M31S: 120_000,

    MachineName.INNOSILICON_T2T: 275_000
}

# Prices by machine
machine_prices = {
    MachineName.ANTMINER_S9: 566.50,
    MachineName.ANTMINER_S17: 4_394.88,
    MachineName.ANTMINER_T17: 2_394.07,
    MachineName.ANTMINER_S19: 6019.00,
    MachineName.ANTMINER_T19: 4922.00,
    MachineName.ANTMINER_S19_PRO: 7388.00,

    MachineName.MICROBT_M20S: 5_674.27,
    MachineName.MICROBT_M21S: 4_231.81,
    MachineName.MICROBT_M30S: 9_989.33,
    MachineName.MICROBT_M31S: 8_385.29,

    MachineName.INNOSILICON_T2T: 1_394.50
}

machine_growth_factors = {
    MachineName.ANTMINER_S9: 0.2,
    MachineName.ANTMINER_S17: 0.4,
    MachineName.ANTMINER_T17: 0.4,
    MachineName.ANTMINER_S19: 1,
    MachineName.ANTMINER_T19: 0.8,
    MachineName.ANTMINER_S19_PRO: 1,

    MachineName.MICROBT_M20S: 0.5,
    MachineName.MICROBT_M21S: 0.5,
    MachineName.MICROBT_M30S: 0.8,
    MachineName.MICROBT_M31S: 0.8,

    MachineName.INNOSILICON_T2T: 0.4
}

machine_setup_times = {
    MachineName.ANTMINER_S9: 14,
    MachineName.ANTMINER_S17: 14,
    MachineName.ANTMINER_T17: 14,
    MachineName.ANTMINER_S19: 48,
    MachineName.ANTMINER_T19: 48,
    MachineName.ANTMINER_S19_PRO: 48,

    MachineName.MICROBT_M20S: 21,
    MachineName.MICROBT_M21S: 21,
    MachineName.MICROBT_M30S: 36,
    MachineName.MICROBT_M31S: 36,

    MachineName.INNOSILICON_T2T: 14
}

# Distribution of strategies
strategy_props = {
    Strategy.SELL_DAILY: 0.5,
    Strategy.LONG_BTC: 0.5
}
