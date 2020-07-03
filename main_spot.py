import sys
from api.model.quant import quant
from strategy.spot_grid_strategy import SpotGridStrategy


def initialize():
    SpotGridStrategy()


def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config/test/eth-config.json"
    quant.initialize(config_file)
    initialize()
    quant.start()


if __name__ == '__main__':
    main()
