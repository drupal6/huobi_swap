import sys
from api.model.quant import quant
from strategy.spot_grid_strategy import SpotGridStrategy
from utils.config import config
from api.model.error import Error


def initialize():
    strategy = config.markets.get("strategy")
    if strategy == "SpotGridStrategy":
        SpotGridStrategy()
    else:
        e = Error(strategy + " not exit.")
        exit(0)


def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config/eth-spot-config.json"
    quant.initialize(config_file)
    initialize()
    quant.start()


if __name__ == '__main__':
    main()
