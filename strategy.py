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

        inputs = indicator.gen_inputs(self.cm.candles)
        rsi_result = indicator.rsi(inputs)
        macd_result = indicator.macd_crossing(inputs)

        logger.debug('RSI: {}'.format(rsi_result))
        logger.debug('MACD: {}'.format(macd_result))

    def candle_update(self, candle):
        pass
