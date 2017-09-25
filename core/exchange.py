import asyncio
import logging

import requests

logger = logging.getLogger(__name__)


class Exchange(object):

    def __init__(self, exchange_id, api_key, api_secret):
        self.id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key,
            'X-API-SECRET': self.api_secret
        }

    def fetch_ticker(self, symbol):
        values = dict(
            exchange_code=self.id,
            exchange_market=symbol
        )
        logger.debug('fetch_ticker: {}'.format(values))
        resp = self.session.post(
            'https://api.coinigy.com/api/v1/ticker',
            json=values
        )

        resp.raise_for_status()
        return resp.json()['data'][0]


class ExchangeLimiter(object):

    def __init__(self, exchange_id, api_key, api_secret, rate_limit_seconds):
        self.id = exchange_id
        self.exchange = Exchange(exchange_id, api_key, api_secret)
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
                result = getattr(self.exchange, attr)(*args, **kwargs)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("ccxt error: {}".format(e))
                await asyncio.sleep(self.rate_limit_seconds)
                continue

            future.set_result(result)
            await asyncio.sleep(self.rate_limit_seconds)
