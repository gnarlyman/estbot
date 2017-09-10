class CandleManager(object):
    """
    Groups price data into time-chunks (candles) based on period_seconds.
    """

    def __init__(self, symbol, exchange, period_seconds):
        """
        :param symbol: COIN/BASE symbol for the market.
        :param exchange: ccxt exchange object id
        :param period_seconds: the candlestick period in seconds
        """
        self.symbol = symbol
        self.exchange = exchange
        self.period_seconds = period_seconds
        self.curr_candle = None
        self.candles = list()

        self.callbacks = dict()

    def tick(self, timestamp_seconds, price):
        """
        Updates the CandleManager with new price info.

        :param timestamp_seconds: the timestamp of the price data
        :param price: the price
        :return:
        """
        time_round = int(timestamp_seconds / self.period_seconds) * self.period_seconds

        if not self.curr_candle:
            self.curr_candle = Candle(self.symbol, self.exchange, time_round, price)
            self.candles.append(self.curr_candle)
            self.trigger('candle_open', self.curr_candle)

        elif self.curr_candle.time == time_round:
            self.curr_candle.update(price)
            self.trigger('candle_update', self.curr_candle)

        else:
            self.trigger('candle_close', self.curr_candle)
            self.curr_candle = Candle(self.symbol, self.exchange, time_round, price)
            self.candles.append(self.curr_candle)
            self.trigger('candle_open', self.curr_candle)

    def trigger(self, event, candle):
        if event in self.callbacks:
            self.callbacks[event](candle)

    def register(self, event, callback):
        self.callbacks.setdefault(event, callback)


class Candle(object):
    """
    Represents a Candle. Tracks key points during a candle's lifetime.
    """
    def __init__(self, symbol, exchange, time, start_price):
        """
        :param symbol:  COIN/BASE symbol for the market.
        :param exchange: ccxt exchange object id
        :param time: the interval period for the candle
        :param start_price: the inital price of the candle
        """
        self.symbol = symbol
        self.exchange = exchange
        self.time = time
        self.open = start_price
        self.high = start_price
        self.low = start_price
        self.close = start_price

    def update(self, price):
        """update high, low and close values and add to volume"""
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.close = price

    def to_dict(self):
        return dict(
            open=self.open,
            close=self.close,
            high=self.high,
            low=self.low
        )
