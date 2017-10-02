import asyncio
import logging
from datetime import datetime, timedelta

import core.candle
import core.trend
import core.trade
import core.schedule
import core.exchange

from core.database import Trades

logger = logging.getLogger(__name__)


class BaseEngine(object):
    """
    This class should be sub-classed by a strategy, where candle functions
    maybe implemented, and strategies created.
    """

    def __init__(self, db_session, ledger, symbol, exchange_id, config):
        """
        :param db_session: a session to the backend database
        :param ledger: the core.ledger.Ledger object for this COIN/BASE/EXCHANGE
        :param symbol: COIN/BASE symbol for the market.
        :param exchange_id: coinigy exchange id
        :param config: config from trade.conf generated by core.util.config_to_dict
        """
        self.db_session = db_session
        self.ledger = ledger
        self.symbol = symbol
        self.coin, self.base = symbol.split('/')
        self.exchange_id = exchange_id
        self.config = config
        self.logger_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id, candle_time=None)

        self.period_seconds = int(self.config['symbols'][symbol]['candle_period_seconds'])
        self.trends = self.config['symbols'][symbol]['trends']
        self.position_size = float(self.config['symbols'][self.symbol]['position_size'])
        self.position_mult = float(self.config['symbols'][self.symbol]['position_mult'])
        self.trade_frequency = int(self.config['symbols'][self.symbol]['trade_frequency'])
        self.paper = bool(self.config['symbols'][self.symbol]['paper'])

        self.candle = self.get_candle_manager()
        self.trend = self.get_trend_manager()
        self.trade = self.get_trade_manager()
        self.schedule = self.get_schedule_manager()

        self.backfill = True

    def get_trade_history(self, history_count):
        query = self.db_session.query(Trades)\
            .filter(Trades.symbol == self.symbol)\
            .filter(Trades.exchange == self.exchange_id)\
            .order_by(Trades.time.desc())\
            .limit(history_count)

        for trade in reversed([i for i in query]):
            yield trade

    @staticmethod
    def get_volume(trade):

        buy_vol = 0
        sell_vol = 0
        if trade.type == 'BUY':
            buy_vol = trade.quantity
        elif trade.type == 'SELL':
            sell_vol = trade.quantity
        return buy_vol, sell_vol

    async def run(self, interval, history_count, pauses=0, stop_at=None, test=False):
        """
        Main loop for candle generation and event handling

        :param interval: frequency to poll database
        :param history_count: number of historical Price objects
                to pull from the database
        :param pauses: useful for stepping through a backfill,
        performing X loops before waiting for user input
        :return:
        """
        logger.debug('engine started', extra=self.logger_extra)

        logger.info('get trade history', extra=self.logger_extra)

        counter = 0
        for trade in self.get_trade_history(history_count):

            buy_vol, sell_vol = self.get_volume(trade)

            self.candle.tick(timestamp=trade.time, price=trade.price, buy_vol=buy_vol, sell_vol=sell_vol)
            counter += 1
            if pauses:
                if counter % pauses == 0:
                    input('{} loops, press return to continue'.format(counter))
            if stop_at:
                if trade.time >= stop_at:
                    return

        logger.info('completed trade history', extra=self.logger_extra)

        # we're done backfilling
        self.backfill = False

        if not test:
            logger.info('monitoring', extra=self.logger_extra)
            while True:
                now = datetime.utcnow()
                for trade in self.db_session.query(Trades) \
                        .filter(Trades.symbol == self.symbol) \
                        .filter(Trades.exchange == self.exchange_id) \
                        .filter(Trades.created_at > now - timedelta(seconds=interval)) \
                        .order_by(Trades.time):

                    buy_vol, sell_vol = self.get_volume(trade)

                    self.candle.tick(timestamp=trade.time, price=trade.price, buy_vol=buy_vol, sell_vol=sell_vol)

                await asyncio.sleep(interval)

    def get_candle_manager(self):
        cm = core.candle.CandleManager(self.symbol, self.exchange_id, self.period_seconds)
        cm.register('candle_open', self.candle_open)
        cm.register('candle_close', self.candle_close)
        cm.register('candle_update', self.candle_update)

        return cm

    def get_trend_manager(self):
        tm = core.trend.TrendManager(
            self.symbol,
            self.exchange_id,
            trends=self.trends,
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
        trade = core.trade.TradeManager(
            base=self.base,
            coin=self.coin,
            symbol=self.symbol,
            exchange_id=self.exchange_id,
            position_size=self.position_size,
            paper=self.paper
        )

        return trade

    def get_schedule_manager(self):
        schedule = core.schedule.ScheduleManager(
            symbol=self.symbol,
            exchange_id=self.exchange_id,
            trade=self.trade,
            ledger=self.ledger,
            frequency=self.trade_frequency,
            position_mult=self.position_mult
        )
        self.trade.add_schedule(schedule)

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
