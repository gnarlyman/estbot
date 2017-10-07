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

    print(config['balances'])
    for coin, options in config['balances'].items():
        core.ledger.Coin.create(coin, options['exchange'], options['supply'])

    with core.ledger.LedgerManager(api_key, api_secret) as ledger_manager:
        engines = list()
        engines.append(ledger_manager.run(interval=60))

        for symbol, options in config['symbols'].items():
            if options['trade'] == '1':
                logger.info('start trading', extra=dict(symbol=symbol, exchange_id=options['exchange']))
                ledger = ledger_manager.get_or_create(symbol, options['exchange'])
                eng = strategy.StrategyA(db_session, ledger, symbol, options['exchange'], config)

                start_at_epoch = options.get('start_at_epoch')
                stop_at_epoch = options.get('stop_at_epoch')

                start_at = None
                stop_at = None
                if start_at_epoch:
                    start_at = datetime.utcfromtimestamp(float(start_at_epoch))
                if stop_at_epoch:
                    stop_at = datetime.utcfromtimestamp(float(stop_at_epoch))

                engines.append(eng.run(
                    interval=1,
                    start_at=start_at,
                    stop_at=stop_at
                ))

        await asyncio.gather(*engines)


if __name__ == '__main__':
    future = asyncio.ensure_future(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(future)
