import sys
from sqlalchemy import Column, ForeignKey, Integer, Float, Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

#Classes

class Movie(Base):
    __tablename__ = 'movie'
    id = Column(Integer, primary_key = True)
    imdb_id = Column(String(20))
    title = Column(String(100), nullable = False)
    poster_url = Column(String(250))

class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key = True)
    name = Column(String(100), nullable = False)
    imdb_id = Column(String(20))

class Roles(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key = True)
    movie_id = Column(String(20), ForeignKey('movie.imdb_id'))
    person_id = Column(String(20), ForeignKey('people.imdb_id'))
    character_name = Column(String(20))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    name = Column(String(20), nullable = False)

class MoviesWatched(Base):
    __tablename__ = 'movies_watched'
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(String(20), ForeignKey('movie.imdb_id'))

engine = create_engine('sqlite:///imdb_recognition.db')

Base.metadata.create_all(engine)
