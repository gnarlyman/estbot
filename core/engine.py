import asyncio
import logging
import time
from datetime import datetime, timedelta

from core import candle as cndl
from core import trade as trd
from core.db_schema import Price

logger = logging.getLogger(__name__)


class BaseEngine(object):
    """
    This class should be sub-classed by a strategy, where candle functions
    maybe implemented, and strategies created.
    """

    def __init__(self, session, symbol, exchange, config, period_seconds):
        """
        :param symbol: COIN/BASE symbol for the market.
        :param exchange: ccxt exchange object id
        :param period_seconds: the candlestick period in seconds
        """
        self.session = session
        self.symbol = symbol
        self.exchange = exchange
        self.period_seconds = period_seconds
        self.config = config
        self.cm = None
        self.tm = None
        self.backfill = True

    async def run(self, interval, history_count):
        """
        Main loop for candle generation and event handling

        :param interval: frequency to poll database
        :param history_count: number of historical Price objects
                to pull from the database
        :return:
        """
        logger.debug('{}-{} engine started'.format(self.symbol, self.exchange))
        self.cm = self.get_candle_manager()
        self.tm = self.get_trade_manager()
        for price in self.session.query(Price) \
                .filter(Price.symbol == self.symbol) \
                .filter(Price.exchange == self.exchange) \
                .order_by(Price.time) \
                .limit(history_count):

            timestamp = time.mktime(price.time.timetuple())
            self.cm.tick(timestamp_seconds=timestamp, price=price.price)

        logger.debug('{}-{} engine backfill completed'.format(self.symbol, self.exchange))

        # we're done backfilling
        self.backfill = False

        while True:
            now = datetime.utcnow()
            for price in self.session.query(Price) \
                    .filter(Price.symbol == self.symbol) \
                    .filter(Price.exchange == self.exchange) \
                    .filter(Price.created_at > now - timedelta(seconds=interval)) \
                    .order_by(Price.time):

                timestamp = time.mktime(price.time.timetuple())
                self.cm.tick(timestamp_seconds=timestamp, price=price.price)

            await asyncio.sleep(interval)

    def get_candle_manager(self):
        cm = cndl.CandleManager(self.symbol, self.exchange, self.period_seconds)
        cm.register('candle_open', self.candle_open)
        cm.register('candle_close', self.candle_close)
        cm.register('candle_update', self.candle_update)
        return cm

    def get_trade_manager(self):
        coin, base = self.symbol.split('/')
        tm = trd.TradeManager(
            base,
            coin,
            self.config['symbols'][self.symbol]['position'],
            self.config['symbols'][self.symbol]['trends'],
            partition_trends=10
        )
        tm.register('trend_up', self.trend_up)
        tm.register('trend_down', self.trend_down)
        tm.register('trend_none', self.trend_none)
        tm.register('trend_price_up', self.trend_price_up)
        tm.register('trend_price_down', self.trend_price_down)
        tm.register('trend_price_none', self.trend_price_none)

        return tm

    def candle_open(self, candle):
        raise NotImplementedError()

    def candle_close(self, candle):
        raise NotImplementedError()

    def candle_update(self, candle):
        raise NotImplementedError()

    def trend_up(self):
        """
        called when the price of a market is trending upward
        :return:
        """
        raise NotImplementedError()

    def trend_down(self):
        """
        called when the price of a market is trending downward
        :return:
        """
        raise NotImplementedError()

    def trend_none(self):
        """
        called when the price of a market is not trending up or down
        :return:
        """
        raise NotImplementedError()

    def trend_price_up(self):
        """
        called when the price reaches a trend line in an upward direction
        :return:
        """
        raise NotImplementedError()

    def trend_price_down(self):
        """
        called when the price reaches a trend line in an downward direction
        :return:
        """
        raise NotImplementedError()

    def trend_price_none(self):
        """
        called when the price trendline has not changed
        :return:
        """
        raise NotImplementedError()