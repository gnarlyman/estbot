import logging
import engine
import talib.abstract
import numpy as np
from datetime import datetime

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

        inputs = dict()
        inputs['close'] = np.array([c.close for c in self.cm.candles])
        close_rsi = talib.abstract.RSI(inputs, dtype=float, price='close', timeperiod=14)
        logger.debug('Close RSI: {}'.format(close_rsi[-1]))

        macd, macdsignal, macdhist = talib.abstract.MACD(
            inputs, price='close', fastperiod=12, slowperiod=26, signalperiod=9)

        logger.debug('MACD: {}, MACDSIGNAL: {}, MACDHIST: {}'.format(
            macd[-1], macdsignal[-1], macdhist[-1]
        ))

    def candle_update(self, candle):
        ts = datetime.fromtimestamp(candle.time)
        logger.debug(
            "{time} UPDATE {symbol}-{exchange} High: {high}, Low: {low}, Open: {open}, Close: {close}".format(
                time=ts.ctime(),
                symbol=candle.symbol,
                exchange=candle.exchange.upper(),
                high=candle.high,
                low=candle.low,
                open=candle.open,
                close=candle.close
            )
        )

        if not self.backfill:
            inputs = dict()
            inputs['close'] = np.array([c.close for c in self.cm.candles])
            close_rsi = talib.abstract.RSI(inputs, dtype=float, price='close', timeperiod=14)
            logger.debug('RSI: {}'.format(close_rsi[-1]))

            macd, macdsignal, macdhist = talib.abstract.MACD(
                inputs, price='close', fastperiod=12, slowperiod=26, signalperiod=9)

            logger.debug('MACD: {}, MACDSIGNAL: {}, MACDHIST: {}'.format(
                macd[-1], macdsignal[-1], macdhist[-1]
            ))
