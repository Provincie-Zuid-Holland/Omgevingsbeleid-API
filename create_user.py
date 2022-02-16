# Creates an API user to use for testing etc
import sys
import pyodbc
from passlib.hash import bcrypt
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from globals import sqlalchemy_database_uri
from Models.gebruikers import Gebruikers 
from db import db 
from passlib.hash import bcrypt

def create_user_encrypt_pw(id, username, password, role, email):
    hashed_pw = bcrypt.hash(password)
    new_user = Gebruikers(ID=id, Gebruikersnaam=username, Wachtwoord=hashed_pw, Rol=role, Email=email)
    # db.session.add(new_user)
    # all_users = db.session.query(Gebruikers_DB_Schema).all()
    # for row in all_users:
    #     print(row['Gebruikersnaam'])
    # db.session.commit()

# This one works (without the app context)
def _create_user_encrypt_pw(id, username, password, role, email):
    engine = create_engine(sqlalchemy_database_uri)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        hashed_pw = bcrypt.hash(password)
        new_user = Gebruikers(ID=id, Gebruikersnaam=username, Wachtwoord=hashed_pw, Rol=role, Email=email)
        session.add(new_user)
        session.commit()

# docker-compose exec api python create_user.py 1 alex lol test alex@pzh.nl
if __name__ == '__main__':
    _create_user_encrypt_pw(*sys.argv[1:])
