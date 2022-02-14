USE master;
GO
IF DB_ID (N'db_dev') IS NULL
CREATE DATABASE db_dev;
GO