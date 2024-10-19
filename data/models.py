from sqlalchemy.orm import relationship
from data.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Relacja z modelem Chat
    chats = relationship("Chat", back_populates="user")
    comments = relationship("Comments", back_populates="user")



class Stocks(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, nullable=False)
    name =  Column(String, nullable=False)
    curr_price = Column(Integer, nullable=False)
    yesterday_price = Column(Integer, nullable=False)
    analyse =  Column(String, nullable=True)
    comments = relationship("Comments", back_populates="stocks")



class Comments(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    date = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    symbol = relationship("Stocks", back_populates="comments")
    user = relationship("Users", back_populates="comments")



class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    comment = Column(String, nullable=False)

    # Relacja z modelem Users
    user = relationship("Users", back_populates="chats")
