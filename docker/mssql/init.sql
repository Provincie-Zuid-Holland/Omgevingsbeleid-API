USE master;
GO
IF DB_ID (N'db_test') IS NULL
CREATE DATABASE db_test;
GO