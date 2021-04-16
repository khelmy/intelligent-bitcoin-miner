# The Intelligent Bitcoin Miner, Part II

## At a Glance

This app simulates the behavior and profitability of Bitcoin miners for The Intelligent Bitcoin Miner Part II.

The code is divided into four main files: `config.py`, which sets user-adjustable parameters; `constants.py`, which sets hard-coded parameters; `CMDataLoader.py`, which fetches historical data from the [Coin Metrics API](https://charts.coinmetrics.io/network-data/); `agents.py`, which specifies agent behavior; `generators.py`, which generates agents according to specified distributions; `Simulator.py`, which specifies the behavior for a simulation run over one or several trials; and `main.py`, which runs simulations and outputs summary plots in `/plots/`.

For more information on the model parameters, please see the attached article or dive into the code!

We use historical price and hashrate data from [Coin Metrics](https://charts.coinmetrics.io/network-data/) and rig price data from [Hashrate Index](https://hashrateindex.com/machines/sha256-rig-index) and General Mining Research to seed our model.

## Installing

This project requires python3 and virtualenv.

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```
python3 main.py
```

## Afterword

Happy hashing!
