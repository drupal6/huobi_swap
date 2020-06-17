"""完成拟合曲线参数计算"""


def liner_fitting(data_x, data_y):
    size = len(data_x)
    i = 0
    sum_xy = 0
    sum_y = 0
    sum_x = 0
    sum_sqare_x = 0
    average_x = 0
    average_y = 0
    while i < size:
        sum_xy += data_x[i] * data_y[i];
        sum_y += data_y[i]
        sum_x += data_x[i]
        sum_sqare_x += data_x[i] * data_x[i]
        i += 1
    average_x = sum_x / size
    average_y = sum_y / size
    return_k = (size * sum_xy - sum_x * sum_y) / (size * sum_sqare_x - sum_x * sum_x)
    return_b = average_y - average_x * return_k
    return [return_k, return_b]


def calculate(data_x, k, b):
    datay = []
    for x in data_x:
        datay.append(k * x + b)
    return datay


def leading_y(x, y):
    """
    预测下个y点值
    :param x:
    :param y:
    :return:
    """
    parameter = liner_fitting(x, y)
    return parameter[0] * (x[-1] + 1) + parameter[1], parameter[0], parameter[1]
