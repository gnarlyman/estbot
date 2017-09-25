import os
import asyncio
import logging.config
from datetime import datetime

import strategy
import core.util as util
from core.database import setup_db


logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


async def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = util.get_config(os.path.join(dir_path, 'trade.conf'))
    logger.debug('CONFIG: {}'.format(config))
    db_session = setup_db(**config['database'])

    engines = list()
    for symbol, options in config['symbols'].items():
        if options['trade'] == '1':
            eng = strategy.StrategyA(db_session, symbol, options['exchange'], config)
            engines.append(eng.run(
                interval=1,
                history_count=10000,
                #stop_at=datetime.strptime("Wed Sep 13 07:05:00 2017", "%a %b %d %H:%M:%S %Y")
            ))

    await asyncio.gather(*engines)


if __name__ == '__main__':
    future = asyncio.ensure_future(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(future)
