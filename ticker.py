import os
import json
import logging
from datetime import datetime
from socketclusterclient import Socketcluster

import core.util as util

from core.database import Trades, setup_db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Ticker(object):

    def __init__(self, tasks, db_session, api_credentials):
        self.tasks = tasks
        self.db_session = db_session
        self.api_credentials = api_credentials

    def subscribe(self, socket):
        for task in self.tasks:
            coin, base = task['symbol'].split('/')
            symbol = "{}--{}".format(coin, base)
            exchange = task['exchange']

            trade_channel = 'TRADE-{exchange}--{symbol}'.format(exchange=exchange, symbol=symbol)

            socket.subscribe(trade_channel)
            socket.onchannel(trade_channel, self.update_db)  # This is used for watching messages over channel

    def update_db(self, _, data):
        symbol = data['label']
        exchange = data['exchange']
        logger.debug("RESULT {symbol}-{exchange} : {result}".format(
            symbol=symbol,
            exchange=exchange,
            result=data['price']
        ))

        trade = Trades()
        trade.symbol = symbol
        trade.exchange = exchange
        trade.price = data['price']
        trade.type = data['type']
        trade.quantity = data['quantity']
        trade.total = data['total']
        trade.time = datetime.strptime(data['time'], "%Y-%m-%dT%H:%M:%S")
        trade.created_at = datetime.utcnow()

        self.db_session.add(trade)
        self.db_session.commit()

    @staticmethod
    def on_set_authentication(socket, token):
        logger.info("Token received " + token)
        socket.setAuthtoken(token)

    def on_authentication(self, socket, isauthenticated):
        logger.info("Authenticated is " + str(isauthenticated))

        def ack(_, __, data):
            logger.debug("token is " + json.dumps(data, sort_keys=True))
            self.subscribe(socket)

        socket.emitack("auth", self.api_credentials, ack)

    def on_connect(self, socket):
        pass

    def on_disconnect(self, socket):
        pass

    def on_connect_error(self, socket, error):
        pass


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = util.get_config(os.path.join(dir_path, 'trade.conf'))
    db_session = setup_db(**config['database'])

    api_credentials = {
        'apiKey': config['coinigy']['api_key'],
        'apiSecret': config['coinigy']['api_secret'],
    }

    tasks = list()
    for symbol, options in config['symbols'].items():
        if options['monitor'] == '1':
            tasks.append(dict(
                exchange=options['exchange'],
                symbol=symbol
            ))

    tick = Ticker(tasks, db_session, api_credentials)

    socket = Socketcluster.socket("wss://sc-02.coinigy.com/socketcluster/")
    socket.setBasicListener(tick.on_connect, tick.on_disconnect, tick.on_connect_error)
    socket.setAuthenticationListener(tick.on_set_authentication, tick.on_authentication)
    socket.setreconnection(True)
    socket.connect()


if __name__ == '__main__':
    main()
