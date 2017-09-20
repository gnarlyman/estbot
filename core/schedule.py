import logging

logger = logging.getLogger(__name__)


class ScheduleManager(object):
    def __init__(self, trade, frequency):
        """
        Manages schedules, prevents duplicate schedule, and expires invalid schedules.

        :param trade: core.trade.Trade object
        """
        self.trade = trade
        self.frequency = frequency

        self.allocations = dict()
        self.distributions = dict()

    def allocate(self, trend_price, curr_price):
        position_count = 3
        if trend_price not in self.allocations:
            self.allocations.update({
                trend_price: Allocation(
                    self.trade,
                    trend_price,
                    curr_price,
                    position_count,
                    self.frequency
                )
            })
            logger.debug(
                'created allocation schedule: Price: {}, '
                'Trend: {}, Pos Count: {}'.format(
                    curr_price, trend_price, position_count
                )
            )

    def distribute(self, trend_price, curr_price):
        position_count = 3
        if trend_price not in self.distributions:
            self.distributions.update({
                trend_price: Distribution(
                    self.trade,
                    trend_price,
                    curr_price,
                    position_count,
                    self.frequency
                )
            })
            logger.debug(
                'created distribution schedule: Price: {}, '
                'Trend: {}, Pos Count: {}'.format(
                    curr_price, trend_price, position_count
                )
            )

    def tick(self, price):
        for allocation in list(self.allocations.values()):
            if price > allocation.start_price:
                allocation.cancel()
                self.allocations.pop(allocation.trend_price)
            elif allocation.positions_executed >= allocation.position_count:
                allocation.done()
                self.allocations.pop(allocation.trend_price)
            else:
                allocation.tick(price)

        for distribution in list(self.distributions.values()):
            if price < distribution.start_price:
                distribution.cancel()
                self.distributions.pop(distribution.trend_price)
            elif distribution.positions_executed >= distribution.position_count:
                distribution.done()
                self.distributions.pop(distribution.trend_price)
            else:
                distribution.tick(price)

        if len(self.allocations) or len(self.distributions):
            logger.debug('Allocation Schedules: {}, Distribution Schedules: {}'.format(
                len(self.allocations), len(self.distributions)
            ))


class Schedule(object):
    def __init__(self, trade, trend_price, curr_price, position_count, frequency):
        """
        Schedule trades over time.

        :param trade: core.trade.Trade object
        :param trend_price: the trend price of this schedule
        :param position_count: the number of positions to execute
        :param frequency: how often to execute schedules (in ticks)
        """

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
        ))

    def done(self):
        logger.debug('finished {}-{} {}/{} from trend: {}'.format(
            self.__class__, self.start_price, self.positions_executed, self.position_count,
            self.trend_price
        ))

    def tick(self, price):
        self.counter += 1
        if self.counter % self.frequency == 0:
            self.positions_executed += 1
            logger.debug('executing {}-{} {}/{} at price: {}, trend: {}'.format(
                self.__class__, self.start_price, self.positions_executed, self.position_count,
                price, self.trend_price
            ))
            self.execute(price)

    def execute(self, price):
        raise NotImplementedError()


class Allocation(Schedule):

    def execute(self, price):
        self.trade.long(price)


class Distribution(Schedule):

    def execute(self, price):
        self.trade.short(price)
