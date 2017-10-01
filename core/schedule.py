import logging

logger = logging.getLogger(__name__)


class ScheduleManager(object):

    def __init__(self, symbol, exchange_id, trade, frequency, position_mult):
        """
        Manages schedules, prevents duplicate schedule, and expires invalid schedules.

        :param trade: core.trade.TradeManager object
        """
        self.symbol = symbol
        self.exchange_id = exchange_id
        self.logger_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id)

        self.trade = trade
        self.frequency = frequency
        self.position_mult = position_mult
        self.positions = list()
        self.allocation_position_count = 1
        self.distribution_position_count = 1

        self.profit_position = None

        self.allocations = dict()
        self.distributions = dict()

    def calculate_profit_position(self):
        if len(self.positions):
            self.profit_position = sum(self.positions)/len(self.positions)

    def event_long(self, price):
        logger.debug('schedule manager received LONG event: {}'.format(price), extra=self.logger_extra)
        self.positions.append(price)

    def event_short(self, price):
        logger.debug('schedule manager received SHORT event: {}'.format(price), extra=self.logger_extra)

    def update_allocation_position_count(self):
        self.distribution_position_count = 1
        self.allocation_position_count = self.allocation_position_count * self.position_mult

    def update_distribution_position_count(self):
        self.allocation_position_count = 1
        self.distribution_position_count = self.distribution_position_count * self.position_mult

    def allocate(self, trend_price, curr_price):
        self.update_allocation_position_count()
        if trend_price not in self.allocations:
            self.allocations.update({
                trend_price: Allocation(
                    self.symbol,
                    self.exchange_id,
                    self.trade,
                    trend_price,
                    curr_price,
                    self.allocation_position_count,
                    self.frequency
                )
            })
            logger.debug(
                'created allocation schedule: Price: {}, '
                'Trend: {}, Pos Count: {}'.format(
                    curr_price, trend_price, self.allocation_position_count
                ), extra=self.logger_extra
            )

    def distribute(self, trend_price, curr_price):
        self.update_distribution_position_count()
        if trend_price not in self.distributions:
            self.distributions.update({
                trend_price: Distribution(
                    self.symbol,
                    self.exchange_id,
                    self.trade,
                    trend_price,
                    curr_price,
                    self.distribution_position_count,
                    self.frequency
                )
            })
            logger.debug(
                'created distribution schedule: Price: {}, '
                'Trend: {}, Pos Count: {}'.format(
                    curr_price, trend_price, self.distribution_position_count
                ), extra=self.logger_extra
            )

    def tick(self, price, latest_candle_time):
        self.logger_extra.update(dict(candle_time=latest_candle_time))

        for allocation in list(self.allocations.values()):
            if price > allocation.start_price:
                allocation.cancel()
                self.allocations.pop(allocation.trend_price)
            elif allocation.positions_executed >= allocation.position_count:
                allocation.done()
                self.allocations.pop(allocation.trend_price)
            else:
                allocation.tick(price, latest_candle_time)

        for distribution in list(self.distributions.values()):
            if price < distribution.start_price:
                distribution.cancel()
                self.distributions.pop(distribution.trend_price)
            elif distribution.positions_executed >= distribution.position_count:
                distribution.done()
                self.distributions.pop(distribution.trend_price)
            else:
                distribution.tick(price, latest_candle_time)

        if len(self.allocations) or len(self.distributions):
            logger.info('Allocation Schedules: {}, Distribution Schedules: {}'.format(
                len(self.allocations), len(self.distributions)
            ), extra=self.logger_extra)

        self.calculate_profit_position()


class Schedule(object):

    def __init__(self, symbol, exchange_id, trade, trend_price, curr_price, position_count, frequency):
        """
        Schedule trades over time.

        :param trade: core.trade.TradeManager object
        :param trend_price: the trend price of this schedule
        :param position_count: the number of positions to execute
        :param frequency: how often to execute schedules (in ticks)
        """
        self.symbol = symbol
        self.exchange_id = exchange_id
        self.logger_extra = dict(symbol=self.symbol, exchange_id=self.exchange_id)

        self.trade = trade
        self.trend_price = trend_price
        self.start_price = curr_price
        self.position_count = position_count
        self.frequency = frequency

        self.counter = 0
        self.positions_executed = 0

    def cancel(self):
        logger.debug('cancelling {}-{} {}/{} from trend: {}'.format(
            self.__class__, self.start_price, self.positions_executed, self.position_count,
            self.trend_price
        ), extra=self.logger_extra)

    def done(self):
        logger.debug('finished {}-{} {}/{} from trend: {}'.format(
            self.__class__, self.start_price, self.positions_executed, self.position_count,
            self.trend_price
        ), extra=self.logger_extra)

    def tick(self, price, latest_candle_time):
        self.logger_extra.update(dict(candle_time=latest_candle_time))

        self.counter += 1
        if self.counter % self.frequency == 0:
            self.positions_executed += 1
            logger.debug('executing {}-{} {}/{} at price: {}, trend: {}'.format(
                self, self.start_price, self.positions_executed, self.position_count,
                price, self.trend_price
            ), extra=self.logger_extra)
            self.execute(price)

        self.trade.tick(price, latest_candle_time)

    def execute(self, price):
        raise NotImplementedError()


class Allocation(Schedule):

    def execute(self, price):
        self.trade.long(price)

    def __repr__(self):
        return "<Allocation>"


class Distribution(Schedule):

    def execute(self, price):
        self.trade.short(price)

    def __repr__(self):
        return "<Distribution>"
