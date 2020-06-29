

def price_ichimoku(last_bar, curr_bar, last_lead, curr_lead):
    """
    价格与云层
    开多：价格上穿云层
    开孔：价格下穿云层
    止盈止损：价格反穿慢线或者价格反穿云层
    :return:
    """
    last_min_lead, last_max_lead = min_max(last_lead, "leada", "leadb")
    min_lead, max_lead = min_max(curr_lead, "leada", "leadb")
    last_close = last_bar["close"]
    close = curr_bar["close"]
    base = curr_bar["base"]
    cur_dir = 0
    charge_dir = 0

    if close > max_lead:
        cur_dir = 1
        if last_close <= last_max_lead:
            charge_dir = 1
    elif close < min_lead:
        cur_dir = -1
        if last_close >= last_min_lead:
            charge_dir = -1
    price_base = 0
    if close < base:
        price_base = -1
    elif close > base:
        price_base = 1
    return cur_dir, charge_dir, price_base


def cb_base_ichimoku(last_bar, curr_bar, curr_lead):
    """
    转换线基准线与云层
    开多:转换线和基准线再云层上方且转换线在基准线上方
    开空:转换线和基准线再云层下方且转换线在基准线下方
    止盈：转换线反穿基准线
    :return:
    """
    min_lead, max_lead = min_max(curr_lead, "leada", "leadb")
    last_conversion = last_bar["conversion"]
    conversion = curr_bar["conversion"]
    last_base = last_bar["base"]
    base = curr_bar["base"]
    cur_dir = 0
    if conversion > max_lead and base > max_lead:
        cur_dir = 1
    elif conversion < min_lead and base < min_lead:
        cur_dir = -1
    cb_dir = 0
    charge_dir = 0
    if conversion > base:
        cb_dir = 1
        if last_conversion <= last_base:
            charge_dir = 1
    elif conversion < base:
        cb_dir = -1
        if last_conversion >= last_base:
            charge_dir = -1
    return cur_dir, charge_dir, cb_dir


def delay_ichimoku(last_bar, curr_bar, last_delay_lead, curr_delay_lead):
    """
    延迟线与云层
    开多：延迟上穿云层
    开孔：延迟下穿云层
    止盈：延迟线反穿云层
    :return:
    """
    last_delay_min_lead, last_delay_max_lead = min_max(last_delay_lead, "leada", "leadb")
    delay_min_lead, delay_max_lead = min_max(curr_delay_lead, "leada", "leadb")
    last_close = last_bar["close"]
    close = curr_bar["close"]
    cur_dir = 0
    charge_dir = 0
    if close > delay_max_lead:
        cur_dir = 1
        if last_close <= last_delay_max_lead:
            charge_dir = 1
    elif close < delay_min_lead:
        cur_dir = -1
        if last_close >= last_delay_min_lead:
            charge_dir = -1
    return cur_dir, charge_dir


def min_max(bar, field1, field2):
    field_value1 = bar[field1]
    field_value2 = bar[field2]
    if field_value1 <= field_value2:
        return field_value1, field_value2
    else:
        return field_value2, field_value1