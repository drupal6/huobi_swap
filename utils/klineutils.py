

def interval_handler(values, periods=[5, 10, 30], vtype="close"):
    ret = dict()
    template_values = dict()
    value_size = len(values)
    for period in periods:
        ret[period] = list()
    temp_index = value_size - 1
    while temp_index >= 0:
        for period in periods:
            if temp_index - period < 0:
                break
            template_values[period] = 0
            for p in range(0, period):
                template_values[period] += float(getattr(values[temp_index - p], vtype))
            ret[period].append(template_values[period]/period)
        temp_index -= 1
    return ret


