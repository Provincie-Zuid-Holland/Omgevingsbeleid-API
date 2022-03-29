# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import datetime
import urllib
import os


# Api version
current_version = "0.1"

# Datetime stuff
min_datetime = datetime.datetime(1753, 1, 1, 0, 0, 0)
max_datetime = datetime.datetime(9999, 12, 31, 23, 59, 59)
null_uuid = default_user_uuid = "00000000-0000-0000-0000-000000000000"

# Search stuff
ftc_name = "Omgevingsbeleid_FTC"
stoplist_name = "Omgevingsbeleid_SW"


# Base configuration which holds for every environment or gets overwritten
class Config():
    JWT_COOKIE_SECURE = True
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")

    # Should probably be 20 minutes
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)

    PROPAGATE_EXCEPTIONS = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    DB_CONNECTION_SETTINGS = f"DRIVER={os.getenv('DB_DRIVER')};SERVER={os.getenv('DB_HOST')};DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASS')}"
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=%s" % DB_CONNECTION_SETTINGS
    SQLALCHEMY_ECHO  = False


class ProdConfig(Config):
    ENV = 'prod'
    PROD = True
    DEBUG = False
    pass


class DevConfig(Config):
    ENV = 'dev'
    PROD = False
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    pass


class TestConfig(Config):
    ENV = 'test'
    PROD = False
    DEBUG = True
    TESTING = True
    SQLALCHEMY_ECHO = False

    # @note: https://stackoverflow.com/questions/26647032/py-test-to-test-flask-register-assertionerror-popped-wrong-request-context
    PRESERVE_CONTEXT_ON_EXCEPTION = False

    DB_CONNECTION_SETTINGS = f"DRIVER={os.getenv('DB_DRIVER')};SERVER={os.getenv('DB_HOST')};DATABASE={os.getenv('TEST_DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASS')}"
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=%s" % DB_CONNECTION_SETTINGS
    
    pass
