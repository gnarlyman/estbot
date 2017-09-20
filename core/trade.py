import logging

logger = logging.getLogger(__name__)


class Trade(object):
    def __init__(self, base, coin, exchange, position_size, paper=False):
        """
        Trade class is used to initiate trades. Trades will be fired upon optimal market conditions.

        :param base: symbol for base currency (e.g. USD)
        :param coin: symbol for market currency (e.g. BTC)
        :param exchange: core.exchangelimiter object for the exchange we want to trade
        :param position_size: how large is one position (in base currency)? (e.g. 0.001 BASE)
        :param paper: true means we don't really trade, only on paper
        """

        self.base = base
        self.coin = coin
        self.exchange = exchange
        self.position_size = position_size
        self.paper = paper

    def long(self, price):
        logger.debug('received Long request at {}'.format(price))

    def short(self, price):
        logger.debug('received Short request at {}'.format(price))
