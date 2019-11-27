import settings
import urllib
import datetime 

# Database stuff
db_connection_settings = f"DRIVER={{{settings.DB_DRIVER}}};SERVER={settings.DB_HOST};DATABASE={settings.DB_NAME};UID={settings.DB_USER};PWD={settings.DB_PASS}"
params = urllib.parse.quote_plus(db_connection_settings)
db_connection_string = "mssql+pyodbc:///?odbc_connect=%s" % params

# Datetime stuff
min_datetime = datetime.datetime(1753, 1, 1, 0, 0, 0)
max_datetime = datetime.datetime(9999, 12, 31, 23, 59, 59)
default_user_uuid = "00000000-0000-0000-0000-000000000000"