from utils import tools
from utils.dingding import DingTalk


class MsgUtil:

    @classmethod
    def order_msg(cls, order):
        if 6 < order["status"] < 4:
            return
        topic = order["topic"]  # 推送的主题
        ts = tools.ts_to_datetime_str(order["ts"]/1000)  # 服务端应答时间戳
        created_at = tools.ts_to_datetime_str(order["created_at"]/1000)  # 订单创建时间
        volume = order["volume"]  # 委托数量
        price = order["price"]  # 委托价格
        order_price_type = order["order_price_type"]  # 订单报价类型 "limit":限价 "opponent":对手价 "post_only":只做maker单,post only下单只受用户持仓数量限制
        direction = order["direction"]  # "buy":买 "sell":卖
        offset = order["offset"]  # "open":开 "close":平
        status = cls.get_status(order["status"])  # 订单状态(1准备提交 2准备提交 3已提交 4部分成交 5部分成交已撤单 6全部成交 7已撤单)
        lever_rate = order["lever_rate"]  # 杠杆倍数
        order_type = order["order_type"]  # 订单类型 1:报单 、 2:撤单 、 3:强平、4:交割
        trade_volume = order["trade_volume"]  # 成交数量
        trade_turnover = order["trade_turnover"]  # 成交总金额
        fee = order["fee"]  # 手续费
        trade_avg_price = order["trade_avg_price"]  # 成交均价
        profit = order["profit"]  # 收益
        msg = "%s\ntopic:%s\ncreate_at:%s\nvolume:%s\nprice:%s\norder_price_type:%s\ndirection:%s\noffset:%s\n" \
              "status:%s\nlever_rate:%s\norder_type:%s\ntrade_volume:%s\ntrade_turnover:%s\ntrade_avg_price:%s\n" \
              "profit:%s\nfee:%s" % (ts, topic, created_at, volume, price, order_price_type, direction, offset, status,
                             lever_rate, order_type, trade_volume, trade_turnover, trade_avg_price, profit, fee)

        DingTalk.send_text_msg(content=msg)



    @classmethod
    def get_status(cls, status):
        if status == 4:
            return "部分成交"
        elif status == 5:
            return "部分成交已撤单"
        elif status == 6:
            return "全部成交"

