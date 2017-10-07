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

        self.ledger_list = dict()

    async def run(self, interval):
        while True:
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

        c, b = self.symbol.split('/')
        self.coin = Coin.get(c, self.exchange_id)
        self.base = Coin.get(b, self.exchange_id)

        logger.info('ledger initialized: {}={} {}={}'.format(
            self.coin.coin,
            self.coin.supply,
            self.base.coin,
            self.base.supply
        ), extra=self.logger_extra)

    def tick(self):
        pass

    def add_long(self, price):
        logger.debug('ledger long added {}'.format(price), extra=self.logger_extra)

    def add_short(self, price):
        logger.debug('ledger short added {}'.format(price), extra=self.logger_extra)


class Coin(object):

    __coins__ = dict()

    def __init__(self, coin, exchange_id, supply):
        self.coin = coin
        self.exchange_id = exchange_id
        self.supply = supply

        self.logger_extra = dict(symbol=self.coin, exchange_id=self.exchange_id)

        logger.info('coin initialied at {}'.format(self.supply), extra=self.logger_extra)

    @staticmethod
    def create(coin, exchange_id, supply):
        coin_id = '{}:{}'.format(coin, exchange_id)
        if coin_id in Coin.__coins__:
            raise Exception('coin {} already exists'.format(coin_id))

        Coin.__coins__.update({
            coin_id: Coin(coin, exchange_id, supply)
        })

        return Coin.__coins__[coin_id]

    @staticmethod
    def get(coin, exchange_id):
        coin_id = '{}:{}'.format(coin, exchange_id)
        return Coin.__coins__[coin_id]
