import logging
from datetime import datetime

import indicator
from core import engine

logger = logging.getLogger(__name__)


def rsi_check(candles):
    inputs = indicator.gen_inputs(candles, 'close')
    return indicator.rsi(inputs, 'close')


class StrategyA(engine.BaseEngine):
    """
    self.cm - access candle manager
    self.cm.candels - list of candles kept in memory
    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.logger_strategy_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id, candle_time=None)

    def candle_open(self, candle):
        self.logger_strategy_extra.update(dict(candle_time=self.candle.curr_candle_time))

        ts = datetime.fromtimestamp(candle.time)
        logger.debug('candle_open {:%m-%d-%Y %H:%M:%S}'.format(ts), extra=self.logger_strategy_extra)

    def candle_close(self, candle):
        self.logger_strategy_extra.update(dict(candle_time=self.candle.curr_candle_time))

        ts = datetime.fromtimestamp(candle.time)
        logger.debug('candle_close {:%m-%d-%Y %H:%M:%S}'.format(ts), extra=self.logger_strategy_extra)
        self.trend.tick(self.candle.candles, self.candle.curr_candle_time)
        self.schedule.tick(self.trend.curr_price, self.candle.curr_candle_time)

        logger.debug(
            "{time:%m-%d-%Y %H:%M:%S} CLOSE High: {high}, Low: {low}, "
            "Open: {open}, Close: {close}, Buy Vol: {buy_vol}, Sell Vol: {sell_vol}, Profit Pos: {profit}".format(
                time=ts,
                high=candle.high,
                low=candle.low,
                open=candle.open,
                close=candle.close,
                buy_vol=candle.total_buy_vol,
                sell_vol=candle.total_sell_vol,
                profit=self.schedule.profit_position
            ),
            extra=self.logger_strategy_extra
        )

        rsi_result = rsi_check(self.candle.candles)

        if rsi_result == 1:
            self.schedule.allocate(self.trend.curr_trend_price, self.trend.curr_price)
        elif rsi_result == -1:
            self.schedule.distribute(self.trend.curr_trend_price, self.trend.curr_price)

    def candle_update(self, candle):
        self.logger_strategy_extra.update(dict(candle_time=self.candle.curr_candle_time))

    def trend_up(self):
        logger.debug('trend_up: {} > {} - TP: {}'.format(
            self.trend.curr_price,
            self.trend.prev_price,
            self.trend.curr_trend_price
        ), extra=self.logger_strategy_extra)

    def trend_down(self):
        logger.debug('trend_down: {} < {} - TP: {}'.format(
            self.trend.curr_price,
            self.trend.prev_price,
            self.trend.curr_trend_price
        ), extra=self.logger_strategy_extra)

    def trend_none(self):
        logger.debug('trend_none: {} == {} - TP: {}'.format(
            self.trend.curr_price,
            self.trend.prev_price,
            self.trend.curr_trend_price
        ), extra=self.logger_strategy_extra)

    def trend_price_up(self):
        logger.debug('trend_price_up: {}'.format(self.trend.curr_trend_price), extra=self.logger_strategy_extra)
        #self.schedule.distribute(self.trend.curr_trend_price, self.trend.curr_price)

    def trend_price_down(self):
        logger.debug('trend_price_down: {}'.format(self.trend.curr_trend_price), extra=self.logger_strategy_extra)
        #self.schedule.allocate(self.trend.curr_trend_price, self.trend.curr_price)

    def trend_retrace_up(self):
        logger.debug('trend_retrace_up: {} > {}'.format(
            self.trend.curr_price, self.trend.curr_trend_price
        ), extra=self.logger_strategy_extra)
        #self.schedule.allocate(self.trend.curr_trend_price, self.trend.curr_price)

    def trend_retrace_down(self):
        logger.debug('trend_retrace_down: {} < {}'.format(
            self.trend.curr_price, self.trend.curr_trend_price
        ), extra=self.logger_strategy_extra)
        #self.schedule.distribute(self.trend.curr_trend_price, self.trend.curr_price)
