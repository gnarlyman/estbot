class ScheduleManager(object):
    def __init__(self, trade, frequency):
        """
        Manages schedules, prevents duplicate schedule, and expires invalid schedules.

        :param trade: core.trade.Trade object
        """
        self.trade = trade
        self.frequency = frequency

        self.allocations = list()
        self.distributions = list()

    def allocate(self, trend_price, position_count):
        self.allocations.append(
            Allocation(
                self.trade,
                trend_price,
                position_count,
                self.frequency
            )
        )

    def distribute(self, trend_price, position_count):
        self.distributions.append(
            Distribution(
                self.trade,
                trend_price,
                position_count,
                self.frequency
            )
        )

    def tick(self, price):
        for allocation in self.allocations[:]:
            if price > allocation.trend_price:
                allocation.cancel()
                self.allocations.remove(allocation)
            elif allocation.positions_executed >= allocation.position_count:
                self.allocations.remove(allocation)
            else:
                allocation.tick(price)

        for distribution in self.distributions[:]:
            if price < distribution.trend_price:
                distribution.cancel()
                self.distributions.remove(distribution)
            elif distribution.positions_executed >= distribution.position_count:
                self.allocations.remove(distribution)
            else:
                distribution.tick(price)


class Schedule(object):
    def __init__(self, trade, type, trend_price, position_count, frequency):
        """
        Schedule trades over time.

        :param trade: core.trade.Trade object
        :param type: allocation or distribution
        :param trend_price: the trend price of this schedule
        :param position_count: the number of positions to execute
        :param frequency: how often to execute schedules (in ticks)
        """

        self.trade = trade
        self.type = type
        self.trend_price = trend_price
        self.position_count = position_count
        self.frequency = frequency

        self.counter = 0
        self.positions_executed = 0

    def cancel(self):
        pass

    def tick(self, price):
        self.counter += 1
        if self.counter % self.frequency == 0:
            self.execute(price)

    def execute(self, price):
        raise NotImplementedError()


class Allocation(Schedule):

    def execute(self, price):
        self.positions_executed += 1
        self.trade.long(price)


class Distribution(Schedule):

    def execute(self, price):
        self.positions_executed += 1
        self.trade.short(price)
