import asyncio
import logging

import ccxt.async as ccxt
import concurrent.futures

logger = logging.getLogger(__name__)


class ExchangeLimiter(object):

    def __init__(self, exchange_id, rate_limit_seconds):
        self.id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)()
        self.queue = list()
        self.rate_limit_seconds = rate_limit_seconds

    async def __call__(self, future, attr, *args, **kwargs):
        request = (future, attr, args, kwargs)
        self.queue.append(request)

    async def run(self):
        while len(self.queue):
            logger.debug("{} request queue: {}".format(self.id, len(self.queue)))
            future, attr, args, kwargs = self.queue.pop(0)
            try:
                result = await getattr(self.exchange, attr)(*args, **kwargs)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("ccxt error: {}".format(e.message))
                await asyncio.sleep(self.rate_limit_seconds)
                continue

            future.set_result(result)
            await asyncio.sleep(self.rate_limit_seconds)
