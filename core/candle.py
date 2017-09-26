import logging

logger = logging.getLogger(__name__)


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

    def tick(self, timestamp_seconds, price, buy_vol, sell_vol):
        """
        Updates the CandleManager with new price info.

        :param timestamp_seconds: the timestamp of the price data
        :param price: the price
        :param buy_vol: how much was bought
        :param sell_vol: how much was sold sold
        :return:
        """
        time_round = int(timestamp_seconds / self.period_seconds) * self.period_seconds

        if not self.curr_candle:
            self.curr_candle = Candle(self.symbol, self.exchange, time_round, price, buy_vol, sell_vol)
            self.candles.append(self.curr_candle)
            self.trigger('candle_open', self.curr_candle)

        elif self.curr_candle.time == time_round:
            self.curr_candle.update(price, buy_vol, sell_vol)
            self.trigger('candle_update', self.curr_candle)

        else:
            self.trigger('candle_close', self.curr_candle)
            self.curr_candle = Candle(self.symbol, self.exchange, time_round, price, buy_vol, sell_vol)
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
    def __init__(self, symbol, exchange, time, start_price, sell_vol, buy_vol):
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
        self.total_sell_vol = sell_vol
        self.total_buy_vol = buy_vol

    def update(self, price, sell_vol, buy_vol):
        """update high, low and close values and add to volume"""
        logger.debug('candle_update Price: {}, Sell: {}, Buy: {}'.format(
            price, sell_vol, buy_vol
        ))
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.close = price
        self.total_sell_vol += sell_vol
        self.total_buy_vol += buy_vol
