import sys
from api.model.quant import quant
from utils.config import config
from api.model.error import Error
from utils import httpserver
from utils.httpserver import MyHttpServer


def initialize():
    strategy = config.markets.get("strategy")
    if strategy == "BollStrategy":
        from strategy.boll_strategy import BollStrategy
        return BollStrategy()
    elif strategy == "EmaStrategy":
        from strategy.ema_strategy import EmaStrategy
        return EmaStrategy()
    elif strategy == "QuantificationStrategy":
        from strategy.quantification_strategy import QuantificationStrategy
        return QuantificationStrategy()
    elif strategy == "IchimokuStrategy":
        from strategy.ichimoku_strategy import IchimokuStrategy
        return IchimokuStrategy()
    elif strategy == "ProfitStrategy":
        from strategy.profit_strategy import ProfitStrategy
        return ProfitStrategy()
    elif strategy == "MACDStrategy":
        from strategy.macd_strategy import MACDStrategy
        return MACDStrategy()
    elif strategy == "GridStrategy":
        from strategy.grid_strategy import GridStrategy
        return GridStrategy()
    else:
        e = Error(strategy + " not exit.")
        exit(0)
    return None


def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config/test/eos-config.json"

    quant.initialize(config_file)
    bs = initialize()
    if bs and config.markets.get("port"):
        ms = MyHttpServer(config.markets.get("port"))
        ms.start()
        httpserver.strategy = bs
    quant.start()


if __name__ == '__main__':
    main()
