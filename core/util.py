import configparser
import bisect


def find_closest(goal, counts):
    return min(sorted(counts, key=lambda i: float(i)), key=lambda x: abs(x - goal))


def find_between(goal, counts, offset=0):
    sorted_counts = sorted(counts, key=lambda i: float(i))
    result = sorted_counts[bisect.bisect_right(sorted_counts, float(goal)) + offset]
    return result


def percent_of_min_max_reversed(min_val, max_val, val):
    return ((max_val - val) / (max_val - min_val)) * 100


def get_trends_from_config(trend_config):
    return list(map(lambda t: float(t), trend_config.split(',')))


def config_to_dict(confparser):
    parsed_config = dict(
        symbols=dict(),
        balances=dict()
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
                if option == 'trends':
                    parsed_config['symbols'][symbol].update({
                        option: get_trends_from_config(value)
                    })
                else:
                    parsed_config['symbols'][symbol].update({
                        option: value
                    })

        elif section == 'database':
            parsed_config['database'] = dict(
                host=confparser.get(section, 'host'),
                port=confparser.get(section, 'port'),
                db_name=confparser.get(section, 'db_name'),
                username=confparser.get(section, 'username'),
                password=confparser.get(section, 'password')
            )

        elif section == 'coinigy':
            parsed_config['coinigy'] = dict(
                api_key=confparser.get(section, 'api_key'),
                api_secret=confparser.get(section, 'api_secret')
            )

        elif section.startswith('balance'):
            _, exchange, coin = section.split(':')
            parsed_config['balances'][coin] = dict(
                exchange=exchange,
                supply=confparser.get(section, 'supply')
            )

    return parsed_config


def get_config(path):
    confparser = configparser.ConfigParser()
    confparser.read(path)
    return config_to_dict(confparser)
