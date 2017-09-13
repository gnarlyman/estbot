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
        self.middle_watch = None
        self.relative_to_middle = None

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

            # compare current price to previous price
            if candles[-1].close > candles[-2].close:
                self.trigger('trend_up')
            elif candles[-1].close < candles[-2].close:
                self.trigger('trend_down')
            else:
                self.trigger('trend_none')

            # track our highs and lows, trigger on crossing
            if not self.curr_trend_price:
                self._get_trend_prices(candles[-1].close)

            if candles[-1].close > self.upper_watch:
                self._get_trend_prices(candles[-1].close)
                self.trigger('trend_price_up')
            elif candles[-1].close < self.lower_watch:
                self._get_trend_prices(candles[-1].close)
                self.trigger('trend_price_down')

            # track our present middle, trigger on crossing
            if not self.relative_to_middle:
                self._get_relative_to_middle(candles[-1].close)
            else:
                if candles[-1].close > self.middle_watch and self.relative_to_middle < 0:
                    self._get_relative_to_middle(candles[-1].close)
                    self.trigger('trend_price_up')
                elif candles[-1].close < self.middle_watch and self.relative_to_middle > 0:
                    self._get_relative_to_middle(candles[-1].close)
                    self.trigger('trend_price_down')

    def _get_relative_to_middle(self, latest_price):
        if latest_price > self.middle_watch:
            self.relative_to_middle = 1
        elif latest_price < self.middle_watch:
            self.relative_to_middle = 1
        else:
            self.relative_to_middle = 0

    def _get_trend_prices(self, latest_price):
        """
        identify the nearest trend to the latest price
        also identify the trend above, and the trend below
        :param latest_price: the latest price
        :return:
        """
        self.curr_trend_price = util.find_closest(latest_price, list(self.trends.keys()))
        trends = sorted(list(self.trends.keys()), key=lambda i: float(i))
        self.upper_watch = trends[trends.index(self.curr_trend_price) + 1]
        self.middle_watch = trends[trends.index(self.curr_trend_price)]
        self.lower_watch = trends[trends.index(self.curr_trend_price) - 1]

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
