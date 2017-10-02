import logging
import asyncio
import core.exchange

logger = logging.getLogger(__name__)


class LedgerManager(object):

    def __init__(self, api_key, api_secret, exchange_limit=1):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange_limit = exchange_limit

        self.logger_extra = dict(symbol=None, exchange_id=None)
        logger.debug('ledger-manager init', extra=self.logger_extra)

        self.ledger_list = dict()

    async def run(self, interval):
        while True:
            logger.debug('ledger tick', extra=self.logger_extra)
            for ledger in self.ledger_list.values():
                ledger.tick()
            await asyncio.sleep(interval)

    def get_or_create(self, symbol, exchange_id):
        exchange = core.exchange.ExchangeLimiter(
            symbol, exchange_id, self.api_key, self.api_secret, self.exchange_limit
        )

        ledger_name = '{}-{}'.format(symbol, exchange_id)
        if ledger_name not in self.ledger_list:
            logger.debug('created ledger {}'.format(ledger_name), extra=dict(symbol=symbol, exchange_id=exchange_id))
            self.ledger_list.update({
                ledger_name: Ledger(symbol, exchange_id, exchange)
            })

        ledger = self.ledger_list[ledger_name]
        return ledger

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def load(self):
        pass

    def save(self):
        pass


class Ledger(object):

    def __init__(self, symbol, exchange_id, exchange):
        self.symbol = symbol
        self.exchange_id = exchange_id
        self.exchange = exchange

        self.logger_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id)

    def tick(self):
        pass

    def add_long(self, price):
        logger.debug('ledger long added {}'.format(price), extra=self.logger_extra)

    def add_short(self, price):
        logger.debug('ledger short added {}'.format(price), extra=self.logger_extra)
