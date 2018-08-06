import pyodbc
import random
import string
from globals import db_connection_string, db_connection_settings
from passlib.hash import bcrypt


def new_client_creds(client_identifier):
    new_cred = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
    new_cred_hash = bcrypt.hash(new_cred)
    connection = pyodbc.connect(db_connection_settings)
    try:
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM dbo.Clients WHERE identifier = ?""", client_identifier)
        if not cursor.fetchone():
            return f"ERROR: Client identifier not found: {client_identifier}"
        cursor.execute("""UPDATE dbo.Clients
                        SET password = ?
                        WHERE identifier = ?""", new_cred_hash, client_identifier)
        connection.commit()
    except pyodbc.Error as odbcex:
        connection.close()
        return f"ERROR: Client identifier not found: {odbcex}"
    return f"Client {client_identifier} new credentials:\n{new_cred}"

