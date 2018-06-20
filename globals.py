import settings
import urllib

# db_connection_string = f"mssql+pyodbc://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?driver={settings.DB_DRIVER}"
# print(db_connection_string)

db_connection_settings = f"DRIVER={{{settings.DB_DRIVER}}};SERVER={settings.DB_HOST};DATABASE={settings.DB_NAME};UID={settings.DB_USER};PWD={settings.DB_PASS}"
params = urllib.parse.quote_plus(db_connection_settings)
db_connection_string = "mssql+pyodbc:///?odbc_connect=%s" % params