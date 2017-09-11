import configparser
from functools import reduce


def find_closest(goal, counts):
    return reduce((lambda curr, prev: abs(curr - goal) < abs(prev - goal)), counts)


def config_to_dict(confparser):
    parsed_config = dict(
        symbols=dict()
    )
    for section in confparser.sections():
        if section.startswith('symbol:'):
            _, exchange, symbol = section.split(':')

            parsed_config['symbols'][symbol] = dict(
                exchange=exchange,
                monitor=0,
                trade=0
            )

            for option in confparser.options(section):
                value = confparser.get(section, option)

                parsed_config['symbols'][symbol].update({
                    option: value
                })
        if section == 'database':
            parsed_config['database'] = dict(
                host=confparser.get(section, 'host'),
                port=confparser.get(section, 'port'),
                db_name=confparser.get(section, 'db_name'),
                username=confparser.get(section, 'username'),
                password=confparser.get(section, 'password')
            )

    return parsed_config


def get_config(path):
    confparser = configparser.ConfigParser()
    confparser.read(path)
    return config_to_dict(confparser)
