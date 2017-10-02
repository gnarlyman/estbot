import os
import asyncio
import logging.config
from datetime import datetime

import strategy
import core.util as util
from core.database import setup_db
import core.ledger


logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


async def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = util.get_config(os.path.join(dir_path, 'trade.conf'))
    db_session = setup_db(**config['database'])

    api_key = config['coinigy']['api_key']
    api_secret = config['coinigy']['api_secret']

    with core.ledger.LedgerManager(api_key, api_secret) as ledger_manager:
        engines = list()
        engines.append(ledger_manager.run(interval=60))

        for symbol, options in config['symbols'].items():
            if options['trade'] == '1':
                logger.info('start trading', extra=dict(symbol=symbol, exchange_id=options['exchange']))
                ledger = ledger_manager.get_or_create(symbol, options['exchange'])
                eng = strategy.StrategyA(db_session, ledger, symbol, options['exchange'], config)
                engines.append(eng.run(
                    interval=1,
                    history_count=50000,
                    #stop_at=datetime.strptime("Wed Sep 13 07:05:00 2017", "%a %b %d %H:%M:%S %Y")
                ))

        await asyncio.gather(*engines)


if __name__ == '__main__':
    future = asyncio.ensure_future(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(future)
