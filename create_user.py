# Creates an API user to use for testing etc
import sys
import pyodbc
from passlib.hash import bcrypt
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from globals import sqlalchemy_database_uri
from Models.gebruikers import Gebruikers_DB_Schema 
from db import db 

def create_user_encrypt_pw(id, username, password, role, email):
    new_user = Gebruikers_DB_Schema(ID=id, UUID='e583401c-e2dd-4202-81c9-9c29f24e3404', Gebruikersnaam=username, Wachtwoord=password, Rol=role, Email=email)
    print(new_user)
    # db.session.add(new_user)
    # all_users = db.session.query(Gebruikers_DB_Schema).all()
    # for row in all_users:
    #     print(row['Gebruikersnaam'])
    # db.session.commit()
    
