from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
Base = declarative_base()


class Price(Base):
    __tablename__ = 'price'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    exchange = Column(String)
    price = Column(Float)
    time = Column(DateTime)
    created_at = Column(DateTime)


def setup_db():
    engine = create_engine('postgresql://pgadmin:postgres@localhost/ccxtbot')
    Base.metadata.create_all(engine)

    sm = sessionmaker(bind=engine)
    session = sm()

    return session
