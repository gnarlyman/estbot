ESTBOT - Extremely Specific Trading Bot
======

This bot is not going to automatically make you rich.

ESTBOT is design to be a simple as possible, and implements
high level concepts like a Strategy, TradeManager, and Scheduling.

Users should choose a market carefully, performing their own
technical analysis, make a plan, and configure the bot to trade
that plan.

Installation
======

A postgres database is required. Use docker to start one easily:
Example:
```
docker run --rm --name dev-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=pgadmin -v ~/postgres-dev:/var/lib/postgresql/data -p 5432:5432 -d postgres
```

You must create a database in postgres:
```
psql -h localhost -U pgadmin
(enter password)
CREATE DATABASE <db_name>;
\q
```

Configuration
===


Usage
======

ccxt python library enables communication to many exchanges:
https://github.com/kroitor/ccxt

See above for complete list of exchanges.
