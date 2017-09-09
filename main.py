import asyncio
import logging

import strategy

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    eng = strategy.StrategyA('BTC/USDT', 'bittrex', period_seconds=60)
    await eng.run()

future = asyncio.ensure_future(main())
loop = asyncio.get_event_loop()
loop.run_until_complete(future)
