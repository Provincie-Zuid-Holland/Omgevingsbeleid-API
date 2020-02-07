import pyodbc
import random
import string
from globals import db_connection_string, db_connection_settings
from passlib.hash import bcrypt
import records

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

def new_client_creds_gebruikers():
    db = records.Database(db_connection_string)
    row = db.query("""SELECT * FROM Gebruikers   WHERE Wachtwoord IS NULL AND UUID != '00000000-0000-0000-0000-000000000000'""")
    result = []
    for user in row:
        new_cred = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        new_cred_hash = bcrypt.hash(new_cred)
        db = records.Database(db_connection_string)
        row = db.query("""UPDATE Gebruikers SET Wachtwoord = :creds WHERE UUID = :uuid""", creds=new_cred_hash, uuid=user['UUID'])
        result.append((user['Gebruikersnaam'], new_cred))

    return result

    #  if not cursor.fetchone():
    #     return f"ERROR: Client identifier not found: {client_identifier}"
    #     cursor.execute("""UPDATE dbo.Clients
    #                     SET password = ?
    #                     WHERE identifier = ?""", new_cred_hash, client_identifier)
    #     connection.commit()

