
"""
RDS Postgres client

Tables:
    user_info
        - id
        - username
        - first name
        - last name
        - password
        - email
        - bucket
    files
        - bucket
        - key
        - uploaded time
        - updated time
        - description


"""
from sqlalchemy import (Column, ForeignKey, PrimaryKeyConstraint)
from sqlalchemy import (Integer, String, DateTime, Date, Text, Float)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class UserInfo(Base):

    __tablename__ = 'user_info'

    uuid = Column(String(256), nullable=False, primary_key=True)
    firstname = Column(String(256), nullable=False)
    lastname = Column(String(256), nullable=False)
    password = Column(String(256), nullable=False)
    email = Column(String(256), nullable=False) #Needs email validation
    created_date = Column(DateTime(timezone=True), nullable=False)
    #bucket = Column(String(256), nullable=False) #username-<uuid>

class FileInfo(Base):

    __tablename__ = 'file_info'
    uuid = Column(String(256), nullable=False, primary_key=True)
    filename = Column(String(256), nullable=False)
    uploaded_time = Column(DateTime(timezone=True), nullable=False)
    updated_time = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(256), nullable=False)
    owner = Column(String(256), ForeignKey('user_info.uuid'), nullable=True)
    user_info = relationship("UserInfo")


  

