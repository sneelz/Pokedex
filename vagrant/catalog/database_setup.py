from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'         : self.id,
           'name'       : self.name,
           'email'      : self.email,
       }

class Pokemon(Base):
    __tablename__ = 'pokemon'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    number = Column(Integer, nullable=False)
    picture = Column(String(250))
    type1 = Column(String(250), nullable=False)
    type2 = Column(String(250))
    description = Column(String(250))
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return { 
           'id'           : self.id,
           'name'         : self.name,
           'number'       : self.number,
           'type1'        : self.type1,
           'type2'        : self.type2,
           'description'  : self.description,
           'picture'      : self.picture,
       }

class Spotted(Base):
    __tablename__ = 'spotted'
   
    id = Column(Integer, primary_key=True)
    location = Column(String(250), nullable=False)
    date = Column(String(250), nullable=False)
    notes = Column(String(250))
    pokemon_id = Column(Integer,ForeignKey('pokemon.id'))
    pokemon = relationship(Pokemon)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'           : self.id,
           'location'     : self.location,
           'date'         : self.date,
           'notes'        : self.notes,
           'pokemon_id'   : self.pokemon_id,
       }


engine = create_engine('sqlite:///pokedexdb.db')

Base.metadata.create_all(engine)