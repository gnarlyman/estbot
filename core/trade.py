import core.util as util


class TradeManager(object):

    def __init__(self, base, coin, position, trends, position_count=1):
        """

        :param base: symbol for base currency (e.g. USD)
        :param coin: symbol for market currency (e.g. BTC)
        :param position: where our profit line is
        :param position_count: how many positions bought
        :param trends: historical or estimated support/resistence lines
            key: price location in market
            value: percentage of COIN investment
            Example: {
                4500: 20
                4000: 50
                3500: 80
            }
        """
        self.base = base
        self.coin = coin
        self.position = position
        self.position_count = position_count
        self.trends = trends

        self.positions = list(self.position,)
        self.curr_trend_price = None
        self.prev_trend_price = None

        self.callbacks = dict()

    def tick(self, candles):
        if len(candles) >= 2:
            if candles[-1].close > candles[-2].close:
                self.trigger('trend_up')
            elif candles[-1].close < candles[-2].close:
                self.trigger('trend_down')
            else:
                self.trigger('trend_none')

            self.prev_trend_price = self.curr_trend_price
            self.curr_trend_price = util.find_closest(candles[-1].close, self.trends.keys())

            if self.curr_trend_price > self.prev_trend_price:
                self.trigger('trend_price_up')
            elif self.curr_trend_price < self.prev_trend_price:
                self.trigger('trend_price_down')
            else:
                self.trigger('trend_price_none')

    def trigger(self, event):
        if event in self.callbacks:
            self.callbacks[event](self)

    def register(self, event, callback):
        self.callbacks.setdefault(event, callback)


class Schedule(object):

    def __init__(self):
        pass
