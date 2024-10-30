from datetime import date

from sqlalchemy import Integer, String, Float, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Mapped, mapped_column

raw_db_creation_schema = """
BEGIN;
CREATE TABLE IF NOT EXISTS city (
    city_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name_city VARCHAR(50),
    days_delivery INTEGER
);
CREATE TABLE IF NOT EXISTS author (
    author_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name_author VARCHAR(50)
    );
CREATE TABLE IF NOT EXISTS genre (
    genre_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name_genre VARCHAR(30)
);
CREATE TABLE IF NOT EXISTS book (
    book_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(50),
    price REAL,
    amount INTEGER,
    author_id INTEGER REFERENCES author(author_id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genre(genre_id) ON DELETE CASCADE 
);
CREATE TABLE IF NOT EXISTS client(
    client_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name_client VARCHAR(50),
    email VARCHAR(30),
    city_id INTEGER REFERENCES city(city_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS buy(
    buy_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    buy_description TEXT,
    client_id INTEGER REFERENCES client(client_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS buy_book(
    buy_book_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    buy_id INTEGER REFERENCES buy(buy_id) ON DELETE CASCADE,
    book_id INTEGER REFERENCES book(book_id) ON DELETE CASCADE,
    amount INTEGER
);
CREATE TABLE IF NOT EXISTS step(
    step_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name_step VARCHAR(30)
);
CREATE TABLE IF NOT EXISTS buy_step(
    buy_step_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    buy_id INTEGER REFERENCES buy(buy_id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES step(step_id) ON DELETE CASCADE,
    date_step_beg DATE,
    date_step_end DATE
);
END; 
"""


class PreBase:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=PreBase)


class City(Base):
    city_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_city: Mapped[str] = mapped_column(String(50))
    days_delivery: Mapped[int] = mapped_column(Integer)


class Author(Base):
    author_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_author: Mapped[str] = mapped_column(String(50))


class Genre(Base):
    genre_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_genre: Mapped[str] = mapped_column(String(50))


class Book(Base):
    book_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(Float)
    amount: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('author.author_id')
    )
    author = relationship('Author', backref='books')
    genre_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('genre.genre_id')
    )
    genre: relationship('Genre', backref='books')


class Client(Base):
    client_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_client: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(30))
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('city.city_id'))
    city = relationship('City', backref='clients')


class Buy(Base):
    buy_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buy_description: Mapped[str] = mapped_column(Text)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('client.client_id')
    )
    client = relationship('Client', backref='buys')
    books = relationship('BuyBook', backref='buy')
    steps = relationship('BuyStep', backref='buy')


class BuyBook(Base):
    buy_book_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buy_id: Mapped[int] = mapped_column(Integer, ForeignKey('buy.buy_id'))
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey('book.book_id'))
    amount: Mapped[int] = mapped_column(Integer)
    book = relationship('Book', backref='buy_books')


class Step(Base):
    step_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_step: Mapped[str] = mapped_column(String(30))


class BuyStep(Base):
    buy_step_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buy_id: Mapped[int] = mapped_column(Integer, ForeignKey('buy.buy_id'))
    step_id: Mapped[int] = mapped_column(Integer, ForeignKey('step.step_id'))
    step = relationship('Step', backref='buy_steps')
    date_step_beg: Mapped[date] = mapped_column(Date)
    date_step_end: Mapped[date] = mapped_column(Date)
