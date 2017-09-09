import time
import logging
import asyncio

from datetime import datetime, timedelta

import candle as cndl
from db_schema import setup_db, Price

logger = logging.getLogger(__name__)


class BaseEngine(object):

    def __init__(self, symbol, exchange, period_seconds=300):
        self.session = setup_db()
        self.symbol = symbol
        self.exchange = exchange
        self.period_seconds = period_seconds
        self.cm = None
        self.backfill = True

    async def run(self, interval=1, history_count=10000):
        self.cm = self.get_candle_manager()
        for price in self.session.query(Price) \
                .filter(Price.symbol == self.symbol) \
                .filter(Price.exchange == self.exchange) \
                .order_by(Price.time) \
                .limit(history_count):

            timestamp = time.mktime(price.time.timetuple())
            self.cm.tick(timestamp_seconds=timestamp, price=price.price)

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

    def candle_open(self, candle):
        raise NotImplementedError()

    def candle_close(self, candle):
        raise NotImplementedError()

    def candle_update(self, candle):
        raise NotImplementedError()
