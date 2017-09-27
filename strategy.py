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
        ts = datetime.fromtimestamp(candle.time)
        logger.debug('candle_open {:%m-%d-%Y %H:%M:%S}'.format(ts))

    def candle_close(self, candle):
        ts = datetime.fromtimestamp(candle.time)
        logger.debug('candle_close {:%m-%d-%Y %H:%M:%S}'.format(ts))
        self.trend.tick(self.candle.candles)
        self.schedule.tick(self.trend.curr_price)

        if len(self.candle.candles) > 5:
            sell_inputs = indicator.gen_inputs(self.candle.candles, 'total_sell_vol')
            buy_inputs = indicator.gen_inputs(self.candle.candles, 'total_buy_vol')
            sell_ema = indicator.ema(sell_inputs, 'total_sell_vol')
            buy_ema = indicator.ema(buy_inputs, 'total_buy_vol')

            logger.debug('BUY_VOL_EMA: {}, SELL_VOL_EMA: {}'.format(buy_ema[-1], sell_ema[-1]))

        logger.debug(
            "{time:%m-%d-%Y %H:%M:%S} CLOSE {symbol}-{exchange}, High: {high}, Low: {low}, "
            "Open: {open}, Close: {close}, Buy Vol: {buy_vol}, Sell Vol: {sell_vol}".format(
                time=ts,
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
