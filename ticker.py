import asyncio
import ccxt.async as cctx
import logging
import functools
from datetime import datetime
from db_schema import Price, setup_db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

session = setup_db()


def update_db(symbol, exchange, future):
    result = future.result()
    logger.debug(result)

    price = Price()
    price.symbol = symbol
    price.exchange = exchange
    price.price = result['last']
    price.time = result['datetime']
    price.created_at = datetime.utcnow()

    session.add(price)
    session.commit()

async def update_ticker(symbol, exchange, interval=5):
    while True:
        future = asyncio.ensure_future(exchange.fetch_ticker(symbol))
        future.add_done_callback(functools.partial(update_db, symbol, exchange.id))
        await asyncio.sleep(interval)


tickers = list()
tickers.append(asyncio.ensure_future(update_ticker('BTC/USDT', cctx.bittrex())))
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tickers))
