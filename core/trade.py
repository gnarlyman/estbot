import logging

import core.util

logger = logging.getLogger(__name__)


class TradeManager(object):
    def __init__(self, base, coin, symbol, exchange_id, position_size, paper=False):
        """
        Tracks a specific Long or Short trade. Executes trades under optimal conditions, such as a retracement.
        Only one trade is tracked. If subsequent trades are added, they will be merged into the active trade.
        Longs will be added to Longs
        Shorts will be added to Shorts

        :param base: symbol for base currency (e.g. USD)
        :param coin: symbol for market currency (e.g. BTC)
        :param symbol: coin/base pair
        :param exchange_id: the identifier of the exchange
        :param position_size: how large is one position (in base currency)? (e.g. 0.001 BASE)
        :param paper: true means we don't really trade, only on paper
        """

        self.symbol = symbol
        self.exchange_id = exchange_id
        self.logger_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id)
        self.callbacks = dict()

        self.base = base
        self.coin = coin
        self.position_size = position_size
        self.paper = paper

        self.schedule = None

        self.active_trade = None

    def add_schedule(self, schedule):
        self.schedule = schedule

    def cancel(self):
        self.active_trade = None

    def long(self, price):
        logger.debug('received Long request at {}'.format(price), extra=self.logger_extra)

        long = Long(
            symbol=self.symbol,
            exchange_id=self.exchange_id,
            base=self.base,
            coin=self.coin,
            position_size=self.position_size,
            paper=self.paper,
            retrace_percent=0.2,
            price=price
        )

        if self.active_trade and isinstance(self.active_trade, Long):
            self.active_trade + long
        else:
            self.active_trade = long
            self.register_events(self.active_trade)

    def short(self, price):
        logger.debug('received Short request at {}'.format(price), extra=self.logger_extra)

        short = Short(
            symbol=self.symbol,
            exchange_id=self.exchange_id,
            base=self.base,
            coin=self.coin,
            position_size=self.position_size,
            paper=self.paper,
            retrace_percent=0.2,
            price=price
        )

        if self.active_trade and isinstance(self.active_trade, Short):
            self.active_trade + short
        else:
            self.active_trade = short
            self.register_events(self.active_trade)

    def tick(self, price, latest_candle_time):
        self.logger_extra.update(dict(candle_time=latest_candle_time))

        if self.active_trade:
            self.active_trade.tick(price, latest_candle_time)

            if self.active_trade.executed:
                self.active_trade = None

    def register_events(self, trade):
        trade.register('execute_long', self.schedule.event_long)
        trade.register('execute_short', self.schedule.event_short)

    def trigger(self, event, price):
        if event in self.callbacks:
            self.callbacks[event](price)

    def register(self, event, callback):
        self.callbacks.setdefault(event, callback)


class Trade(object):

    def __init__(self, symbol, exchange_id, base, coin, position_size, paper, retrace_percent, price):
        self.symbol = symbol
        self.exchange_id = exchange_id
        self.logger_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id)
        self.callbacks = dict()
        self.type = None

        self.base = base
        self.coin = coin
        self.paper = paper
        self.position_size = position_size
        self.retrace_percent = retrace_percent  # 0.2 == 20%
        self.executed = False

        self.orig = price
        self.high = price
        self.low = price
        self.current = price

    def tick(self, price, latest_candle_time):
        self.logger_extra.update(dict(candle_time=latest_candle_time))

        if price > self.high:
            self.high = price
        elif price < self.low:
            self.low = price
        self.current = price

        self.eval_price()

    def execute(self):
        self.executed = True
        logger.info('executing trade {}: Orig: {}, Low: {}, High: {}, Current: {} -- Size: {}'.format(
            self, self.orig, self.low, self.high, self.current, self.position_size
        ), extra=self.logger_extra)
        self.trigger('execute_{}'.format(self.type), self.current, self.position_size)

    def eval_price(self):
        raise NotImplementedError()

    def __add__(self, other):
        self.position_size += other.position_size

    def trigger(self, event, price, position_size):
        if event in self.callbacks:
            self.callbacks[event](price, position_size)

    def register(self, event, callback):
        self.callbacks.setdefault(event, callback)


class Long(Trade):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.type = 'long'

    def eval_price(self):
        logger.debug('long eval {}: Orig: {}, Low: {}, High: {}, Current: {}'.format(
            self, self.orig, self.low, self.high, self.current
        ), extra=self.logger_extra)
        if self.high > self.current:
            target = self.low + (self.retrace_percent * (self.orig - self.low))
            logger.debug('long Target: {}, Current: {}'.format(target, self.current), extra=self.logger_extra)
            if self.current > target:
                self.execute()

        if self.current > self.orig:
            self.execute()

    def __repr__(self):
        return "<Long>"


class Short(Trade):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.type = 'short'

    def eval_price(self):
        logger.debug('short eval {}: Orig: {}, Low: {}, High: {}, Current: {}'.format(
            self, self.orig, self.low, self.high, self.current
        ), extra=self.logger_extra)
        if self.low < self.current:
            target = self.high - (self.retrace_percent * (self.high - self.orig))
            logger.debug('short Target: {}, Current: {}'.format(target, self.current), extra=self.logger_extra)
            if self.current < target:
                self.execute()

        if self.current < self.orig:
            self.execute()

    def __repr__(self):
        return "<Short>"
