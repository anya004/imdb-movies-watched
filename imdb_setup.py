import sys
import datetime
from sqlalchemy import Table, Column, ForeignKey, Integer, Float, Boolean, DateTime, String, UniqueConstraint, Text
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

    movies_watched_by = relationship("MoviesWatched", back_populates="movie")


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

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key = True)
#     name = Column(String(20), nullable = False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    avatar = Column(String(200))
    active = Column(Boolean, default=False)
    tokens = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())

    movies_watched = relationship("MoviesWatched", back_populates="user")

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return self.id
        except AttributeError:
            raise NotImplementedError('No `id` attribute - override `get_id`')


# Helper table: http://flask-sqlalchemy.pocoo.org/2.1/models/

#movies_watched = Table('movies_watched',
    #Column('movie_id', Integer, ForeignKey('movie.id')),
    #Column('user_id', Integer, ForeignKey('users.id'))
#)

class MoviesWatched(Base):
    __tablename__ = 'movies_watched'
    #id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    movie_id = Column(String(20), ForeignKey('movie.imdb_id'), primary_key=True)
    user = relationship("User", back_populates = 'movies_watched')
    movie = relationship("Movie", back_populates = 'movies_watched_by')

engine = create_engine('sqlite:///imdb_recognition.db')

Base.metadata.create_all(engine)
