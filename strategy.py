import logging
from datetime import datetime

import indicator
from core import engine

logger = logging.getLogger(__name__)


class StrategyA(engine.BaseEngine):
    """
    self.cm - access candle manager
    self.cm.candels - list of candles kept in memory
    """

    def candle_open(self, candle):
        logger.debug('candle_open {}'.format(candle.time))

    def candle_close(self, candle):
        logger.debug('candle_close {}'.format(candle.time))
        self.trend.tick(self.candle.candles)

        ts = datetime.fromtimestamp(candle.time)
        logger.debug(
            "{time} CLOSE {symbol}-{exchange}, High: {high}, Low: {low}, "
            "Open: {open}, Close: {close}, Buy Vol: {buy_vol}, Sell Vol: {sell_vol}".format(
                time=ts.ctime(),
                symbol=candle.symbol,
                exchange=candle.exchange.upper(),
                high=candle.high,
                low=candle.low,
                open=candle.open,
                close=candle.close,
                buy_vol=candle.total_buy_vol,
                sell_vol=candle.total_sell_vol
            )
        )

        inputs = indicator.gen_inputs(self.candle.candles)
        rsi_result = indicator.rsi(inputs)
        macd_result = indicator.macd_crossing(inputs)

        logger.debug('RSI: {}'.format(rsi_result))
        logger.debug('MACD: {}'.format(macd_result))

        logger.debug("trends: {}".format(sorted(self.trend.trends.items(), key=lambda k: int(k[0]))))

        if rsi_result == 1:
            logger.debug('RSI {}: buying'.format(rsi_result))
            self.schedule.allocate(self.trend.middle_watch, self.trend.curr_price)
        elif rsi_result == -1:
            logger.debug('RSI {}: selling'.format(rsi_result))
            self.schedule.distribute(self.trend.middle_watch, self.trend.curr_price)

    def candle_update(self, candle):
        pass

    def trend_up(self):
        logger.debug('trend_up: {} > {} - TP: {}'.format(
            self.trend.curr_price,
            self.trend.prev_price,
            self.trend.curr_trend_price
        ))

    def trend_down(self):
        logger.debug('trend_down: {} < {} - TP: {}'.format(
            self.trend.curr_price,
            self.trend.prev_price,
            self.trend.curr_trend_price
        ))

    def trend_none(self):
        logger.debug('trend_none: {} == {} - TP: {}'.format(
            self.trend.curr_price,
            self.trend.prev_price,
            self.trend.curr_trend_price
        ))

    def trend_price_up(self):
        logger.debug('trend_price_up: {}'.format(self.trend.curr_trend_price))

    def trend_price_down(self):
        logger.debug('trend_price_down: {}'.format(self.trend.curr_trend_price))

    def trend_retrace_up(self):
        logger.debug('trend_retrace_up: {} > {}'.format(self.trend.curr_price, self.trend.curr_trend_price))

    def trend_retrace_down(self):
        logger.debug('trend_retrace_down: {} < {}'.format(self.trend.curr_price, self.trend.curr_trend_price))
