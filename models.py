from sqlalchemy import Column, Integer, String, Float
from database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    sr_no = Column(Integer, nullable=False)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    salary = Column(Integer, nullable=False)
    department = Column(String(50), nullable=False)
    joindate = Column(String(50), nullable=True)
    profile_pic = Column(String(355), nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)