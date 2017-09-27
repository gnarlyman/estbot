import talib.abstract
import numpy as np


def gen_inputs(candles, field):
    inputs = dict()
    inputs[field] = np.array([getattr(c, field) for c in candles])
    return inputs


def rsi(inputs, timeperiod=14, high=70, low=30):
    result = talib.abstract.RSI(inputs, dtype=float, price='close', timeperiod=timeperiod)[-1]
    if result:
        if result < low:
            return 1
        elif result > high:
            return -1
    return 0


def macd_crossing(inputs, fastperiod=12, slowperiod=26, signalperiod=9):
    macd, macdsignal, macdhist = talib.abstract.MACD(
        inputs, price='close',
        fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    if not len(macdhist) >= 2:
        return 0

    mh1 = macdhist[-1]
    mh2 = macdhist[-2]

    if mh2 > 0 > mh1:
        return -1
    elif mh2 < 0 < mh1:
        return 1
    return 0


def ema(inputs, field, timeperiod=10):
    ema_result = talib.abstract.EMA(
        inputs, timeperiod=timeperiod, price=field
    )
    return ema_result
