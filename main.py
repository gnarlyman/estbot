import asyncio
import logging
import gui.main_window

import strategy

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    #eng = strategy.StrategyA('BTC/USDT', 'bittrex', period_seconds=300)
    #await eng.run()
    ui = gui.main_window.MainWindow()
    await ui.run()

future = asyncio.ensure_future(main())
loop = asyncio.get_event_loop()
loop.run_until_complete(future)
