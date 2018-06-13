import settings

db_connection_string = f"mssql+pyodbc://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?driver={settings.DB_DRIVER}"
