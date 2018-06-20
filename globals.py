import settings
import urllib


db_connection_settings = f"DRIVER={{{settings.DB_DRIVER}}};SERVER={settings.DB_HOST};DATABASE={settings.DB_NAME};UID={settings.DB_USER};PWD={settings.DB_PASS}"
params = urllib.parse.quote_plus(db_connection_settings)
db_connection_string = "mssql+pyodbc:///?odbc_connect=%s" % params