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
            "{time} CLOSE {symbol}-{exchange}, High: {high}, Low: {low}, Open: {open}, Close: {close}".format(
                time=ts.ctime(),
                symbol=candle.symbol,
                exchange=candle.exchange.upper(),
                high=candle.high,
                low=candle.low,
                open=candle.open,
                close=candle.close
            )
        )

        inputs = indicator.gen_inputs(self.candle.candles)
        rsi_result = indicator.rsi(inputs)
        macd_result = indicator.macd_crossing(inputs)

        logger.debug('RSI: {}'.format(rsi_result))
        logger.debug('MACD: {}'.format(macd_result))

        logger.debug("trends: {}".format(sorted(self.trend.trends.items(), key=lambda k: int(k[0]))))

    def candle_update(self, candle):
        self.trend.tick(self.candle.candles)

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
