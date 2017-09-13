import logging
import core.util as util

logger = logging.getLogger(__name__)


class TradeManager(object):
    def __init__(self, base, coin, position, trends,
                 position_count=1, partition_trends=0):
        """

        :param base: symbol for base currency (e.g. USD)
        :param coin: symbol for market currency (e.g. BTC)
        :param position: where our profit line is
        :param position_count: how many positions bought
        :param partition_trends: how many trends to fill in gaps
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
        self.position = int(position)
        self.position_count = int(position_count)
        self.partition_trends = int(partition_trends)
        self.trends = self._get_trends(trends)

        self.positions = list((self.position, ))
        self.curr_trend_price = None
        self.upper_watch = None
        self.lower_watch = None

        self.callbacks = dict()

    def _get_trends(self, trends):
        if self.partition_trends > 1:
            trend = None
            perc = None
            for t in list(trends):
                p = trends[t]
                if trend:
                    tspread = abs(trend - t) / self.partition_trends
                    pspread = abs(perc - p) / self.partition_trends
                    for i in range(self.partition_trends):
                        trends.update({
                            t + (tspread * i): p - (pspread * i)
                        })
                trend = t
                perc = p

        logger.debug("processed trends: {}".format(sorted(trends.items(), key=lambda k: int(k[0]))))
        return trends

    def tick(self, candles):
        if len(candles) >= 2:

            if candles[-1].close > candles[-2].close:
                self.trigger('trend_up')
            elif candles[-1].close < candles[-2].close:
                self.trigger('trend_down')
            else:
                self.trigger('trend_none')

            if not self.curr_trend_price:
                self._get_trend_prices(candles)

            if candles[-1].close > self.upper_watch:
                self._get_trend_prices(candles)
                self.trigger('trend_price_up')
            elif candles[-1].close < self.lower_watch:
                self._get_trend_prices(candles)
                self.trigger('trend_price_down')
            else:
                self.trigger('trend_price_none')

    def _get_trend_prices(self, candles):
        self.curr_trend_price = util.find_closest(candles[-1].close, list(self.trends.keys()))

        self.upper_watch = util.find_between(candles[-1].close, list(self.trends.keys()), offset=0)
        self.lower_watch = util.find_between(candles[-1].close, list(self.trends.keys()), offset=-1)
        logger.debug('new trend prices: Upper: {}, Lower: {}, Current: {}'.format(
            self.upper_watch,
            self.lower_watch,
            self.curr_trend_price
        ))

    def trigger(self, event):
        if event in self.callbacks:
            self.callbacks[event]()

    def register(self, event, callback):
        self.callbacks.setdefault(event, callback)


class Schedule(object):
    def __init__(self):
        pass
