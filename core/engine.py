import asyncio
import logging
import time
from datetime import datetime, timedelta

import core.candle
import core.trend
import core.trade
import core.schedule
import core.exchangelimiter

from core.db_schema import Price

logger = logging.getLogger(__name__)


class BaseEngine(object):
    """
    This class should be sub-classed by a strategy, where candle functions
    maybe implemented, and strategies created.
    """

    def __init__(self, db_session, symbol, exchange_id, config):
        """
        :param db_session: a session to the backend database
        :param symbol: COIN/BASE symbol for the market.
        :param exchange_id: ccxt exchange object id
        :param config: config from trade.conf generated by core.util.config_to_dict
        """
        self.db_session = db_session
        self.symbol = symbol
        self.coin, self.base = symbol.split('/')
        self.exchange_id = exchange_id
        self.config = config

        self.period_seconds = int(self.config['symbols'][symbol]['candle_period_seconds'])
        self.partition_trends = int(self.config['symbols'][symbol].get('partition_trends', 0))
        self.trends = self.config['symbols'][symbol]['trends']
        self.position_size = float(self.config['symbols'][self.symbol]['position_size'])
        self.trade_frequency = int(self.config['symbols'][self.symbol]['trade_frequency'])
        self.paper = bool(self.config['symbols'][self.symbol]['paper'])

        self.exchange = self.get_exchange()
        self.candle = self.get_candle_manager()
        self.trend = self.get_trend_manager()
        self.trade = self.get_trade_manager()
        self.schedule = self.get_schedule_manager()

        self.backfill = True

    async def run(self, interval, history_count):
        """
        Main loop for candle generation and event handling

        :param interval: frequency to poll database
        :param history_count: number of historical Price objects
                to pull from the database
        :return:
        """
        logger.debug('{}-{} engine started'.format(self.symbol, self.exchange_id))

        for price in self.db_session.query(Price) \
                .filter(Price.symbol == self.symbol) \
                .filter(Price.exchange == self.exchange_id) \
                .order_by(Price.time) \
                .limit(history_count):

            timestamp = time.mktime(price.time.timetuple())
            self.candle.tick(timestamp_seconds=timestamp, price=price.price)

        logger.debug('{}-{} engine backfill completed'.format(self.symbol, self.exchange_id))

        # we're done backfilling
        self.backfill = False

        while True:
            now = datetime.utcnow()
            for price in self.db_session.query(Price) \
                    .filter(Price.symbol == self.symbol) \
                    .filter(Price.exchange == self.exchange_id) \
                    .filter(Price.created_at > now - timedelta(seconds=interval)) \
                    .order_by(Price.time):

                timestamp = time.mktime(price.time.timetuple())
                self.candle.tick(timestamp_seconds=timestamp, price=price.price)

            await asyncio.sleep(interval)

    def get_exchange(self):
        return core.exchangelimiter.ExchangeLimiter(self.exchange_id, rate_limit_seconds=1)

    def get_candle_manager(self):
        cm = core.candle.CandleManager(self.symbol, self.exchange_id, self.period_seconds)
        cm.register('candle_open', self.candle_open)
        cm.register('candle_close', self.candle_close)
        cm.register('candle_update', self.candle_update)

        return cm

    def get_trend_manager(self):
        tm = core.trend.TrendManager(
            trends=self.trends,
            partition_trends=self.partition_trends
        )
        tm.register('trend_up', self.trend_up)
        tm.register('trend_down', self.trend_down)
        tm.register('trend_none', self.trend_none)
        tm.register('trend_price_up', self.trend_price_up)
        tm.register('trend_price_down', self.trend_price_down)
        tm.register('trend_retrace_up', self.trend_retrace_up)
        tm.register('trend_retrace_down', self.trend_retrace_down)

        return tm

    def get_trade_manager(self):
        trade = core.trade.Trade(
            base=self.base,
            coin=self.coin,
            exchange=self.exchange,
            position_size=self.position_size,
            paper=self.paper
        )

        return trade

    def get_schedule_manager(self):
        schedule = core.schedule.ScheduleManager(
            trade=self.trade,
            frequency=self.trade_frequency)

        return schedule

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

    def trend_retrace_up(self):
        """
        called when the price retraces the middle trend line
        indicates the price was below the middle trend, and moved above
        :return:
        """
        raise NotImplementedError()

    def trend_retrace_down(self):
        """
        called when the price retraces the middle trend line
        indicates the price was above the middle trend, and moved below
        :return:
        """
        raise NotImplementedError()
