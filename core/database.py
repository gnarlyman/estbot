import logging

from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


class Trades(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    exchange = Column(String)
    price = Column(Float)
    type = Column(String)
    quantity = Column(Float)
    total = Column(Float)
    time = Column(DateTime)
    created_at = Column(DateTime)


def setup_db(host, port, db_name, username, password):
    logger.info('setting up database {}:{}/{}'.format(host, port, db_name))
    engine = create_engine('postgresql://{username}:{password}@{host}:{port}/{db_name}'.format(
        host=host,
        port=port,
        db_name=db_name,
        username=username,
        password=password
    ))
    Base.metadata.create_all(engine)

    sm = sessionmaker(bind=engine)
    session = sm()

    return session
