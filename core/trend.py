import logging
import core.util as util

logger = logging.getLogger(__name__)


class TrendManager(object):
    def __init__(self, symbol, exchange_id, trends):
        """
        :param symbol: COIN/BASE symbol for the market.
        :param exchange_id: coinigy exchange id
        :param trends: historical or estimated support/resistence lines
            key: price location in market
            value: percentage of COIN investment
            Example: (4500, 4000, 3500)
        """
        self.logger_extra = dict(symbol=symbol, exchange_id=exchange_id, candle_time=None)
        self.trends = self._get_trends(trends)

        self.curr_price = None
        self.prev_price = None
        self.curr_trend_price = None
        self.upper_watch = None
        self.lower_watch = None
        self.middle_watch = None

        self.callbacks = dict()

    def _get_trends(self, trends):
        trends_percent = dict()
        min_t, max_t = (min(trends), max(trends))
        for t in trends:
            trends_percent.update({t: util.percent_of_min_max_reversed(min_t, max_t, t)})

        logger.debug("processed trends: {}".format(sorted(trends_percent.items(), key=lambda k: int(k[0]))),
                     extra=self.logger_extra)
        return trends_percent

    def tick(self, candles, latest_candle_time):
        self.logger_extra.update(dict(candle_time=latest_candle_time))

        self.prev_price = self.curr_price
        self.curr_price = candles[-1].close

        if self.prev_price and len(candles) >= 2:

            # compare current price to previous price
            if self.curr_price > self.prev_price:
                self.trigger('trend_up')
            elif self.curr_price < self.prev_price:
                self.trigger('trend_down')
            else:
                self.trigger('trend_none')

            # track our highs and lows, trigger on crossing
            if not self.curr_trend_price:
                self._get_trend_prices(self.curr_price)

            if self.curr_price >= self.upper_watch:
                self._get_trend_prices(self.curr_price)
                self.trigger('trend_price_up')
            elif self.curr_price <= self.lower_watch:
                self._get_trend_prices(self.curr_price)
                self.trigger('trend_price_down')
            elif self.prev_price < self.middle_watch < self.curr_price:
                self.trigger('trend_retrace_up')
            elif self.prev_price > self.middle_watch > self.curr_price:
                self.trigger('trend_retrace_down')

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
        ), extra=self.logger_extra)

    def trigger(self, event):
        if event in self.callbacks:
            self.callbacks[event]()

    def register(self, event, callback):
        self.callbacks.setdefault(event, callback)
