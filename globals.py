# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import datetime
import urllib

import os

# Database stuff
db_connection_settings = f"DRIVER={os.getenv('DB_DRIVER')};SERVER={os.getenv('DB_HOST')};DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASS')}"
sqlalchemy_database_uri = "mssql+pyodbc:///?odbc_connect=%s" % db_connection_settings

# Datetime stuff
min_datetime = datetime.datetime(1753, 1, 1, 0, 0, 0)
max_datetime = datetime.datetime(9999, 12, 31, 23, 59, 59)
null_uuid = default_user_uuid = "00000000-0000-0000-0000-000000000000"

# Search stuff
ftc_name = "Omgevingsbeleid_FTC"
stoplist_name = "Omgevingsbeleid_SW"

# Util functions
def row_to_dict(row):
    """
    Turns a row from pyodbc into a dictionary
    """
    return dict(zip([t[0] for t in row.cursor_description], row))
