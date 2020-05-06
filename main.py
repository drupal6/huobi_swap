import sys
from api.model.quant import quant
from utils.config import config
from api.model.error import Error


def initialize():
    strategy = config.markets.get("strategy")
    if strategy == "BollStrategy":
        from strategy.boll_strategy import BollStrategy
        BollStrategy()
    elif strategy == "EmaStrategy":
        from strategy.ema_strategy import EmaStrategy
        EmaStrategy()
    elif strategy == "QuantificationStrategy":
        from strategy.quantification_strategy import QuantificationStrategy
        QuantificationStrategy()
    elif strategy == "QuantificationStrategy1":
        from strategy.quantification_strategy1 import QuantificationStrategy1
        QuantificationStrategy1()
    elif strategy == "IchimokuStrategy":
        from strategy.ichimoku_strategy import IchimokuStrategy
        IchimokuStrategy()
    else:
        e = Error(strategy + " not exit.")
        exit(0)


def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config/config.json"

    quant.initialize(config_file)
    initialize()
    quant.start()


if __name__ == '__main__':
    main()
