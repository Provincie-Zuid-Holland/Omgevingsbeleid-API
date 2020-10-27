import marshmallow as MM
from lxml import html
from globals import min_datetime, max_datetime, db_connection_settings
from flask_restful import Resource
import pyodbc
import datetime
from bs4 import BeautifulSoup
import re


def row_to_dict(row):
    """
    Turns a row from pyodbc into a dictionary
    """
    return dict(zip([t[0] for t in row.cursor_description], row))

with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
    cursor = connection.cursor()
    maatregelen_q = "SELECT * FROM Maatregelen"
    result = cursor.execute(maatregelen_q)
    for row in result.fetchall():
        maatregel = row_to_dict(row)
        if maatregel['Toelichting']:
            maatregelen_update_q = "UPDATE Maatregelen SET Toelichting_Raw = ? WHERE UUID = ?"
            soup = BeautifulSoup(maatregel['Toelichting'], features="lxml")
            titles = soup.find_all(re.compile(r"h\d"))
            for title in titles:
                title.decompose()
            Toelichting_Raw = soup.get_text(" ")
            cursor.execute(maatregelen_update_q, Toelichting_Raw, maatregel['UUID'])
    connection.commit()
