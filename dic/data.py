from sqlalchemy import Boolean, String, Column, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

DeclarativeBase = declarative_base()


class Revision(DeclarativeBase):
    __tablename__ = "revision"

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime)


class Device(DeclarativeBase):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(String)
    device_id = Column(String)
    device_class = Column(String)
    device_status = Column(Boolean)
    revision = Column(Integer, ForeignKey("revision.id"))
