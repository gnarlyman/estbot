import os
import asyncio
import functools
import logging
from datetime import datetime

import core.util as util
import core.exchangelimiter

from core.db_schema import Price, setup_db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

session = setup_db()


def update_db(symbol, exchange, future):
    result = future.result()
    logger.debug("RESULT {symbol}-{exchange} : {result}".format(
        symbol=symbol,
        exchange=exchange,
        result=result['last']
    ))

    price = Price()
    price.symbol = symbol
    price.exchange = exchange
    price.price = result['last']
    price.time = result['datetime']
    price.created_at = datetime.utcnow()

    session.add(price)
    session.commit()

async def update_ticker(symbol, exch, interval):
    while True:
        future = asyncio.Future()
        future.add_done_callback(functools.partial(update_db, symbol, exch.id))
        asyncio.ensure_future(exch(future, 'fetch_ticker', symbol))
        await asyncio.sleep(interval)


async def update_exchange(exch, interval):
    while True:
        await exch.run()
        await asyncio.sleep(interval)


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = util.get_config(os.path.join(dir_path, 'trade.conf'))

    tasks = list()
    exchanges = dict()
    for symbol, options in config['symbols'].items():
        if options['monitor'] == '1':
            e = options['exchange']
            if e not in exchanges:
                exch = core.exchangelimiter.ExchangeLimiter(e, rate_limit_seconds=1)
                logger.debug("{}: exchange created".format(exch.id))
                exchanges.setdefault(e, exch)
                tasks.append(asyncio.Task(update_exchange(exch, interval=2)))

    for symbol, options in config['symbols'].items():
        if options['monitor'] == '1':
            exch = exchanges[options['exchange']]
            tasks.append(asyncio.ensure_future(update_ticker(symbol, exch, interval=10)))

    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(asyncio.gather(*tasks))

if __name__ == '__main__':
    main()
