USE db_test;
GO
EXEC sp_MSforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT all";
GO
EXEC sp_MSforeachtable "DROP TABLE ?";
GO