SELECT MAX(LEN(Wachtwoord)) as MaxLength 
FROM Gebruikers;



ALTER TABLE Gebruikers
ALTER COLUMN Wachtwoord nvarchar(500);

ALTER TABLE Werkingsgebieden
ALTER COLUMN Werkingsgebied nvarchar(500);


CREATE TABLE Gebruikers (
	ID int DEFAULT NEXT VALUE FOR [seq_Gebruikers] NOT NULL,
	UUID uniqueidentifier DEFAULT newid() NOT NULL,
	Gebruikersnaam nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Wachtwoord nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Rol nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Email nvarchar(265) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'Actief' NULL,
	CONSTRAINT PK_Gebruikers PRIMARY KEY (UUID)
);


CREATE SEQUENCE seq_Werkingsgebieden
    AS INT
    START WITH 100
    INCREMENT BY 1;




SELECT MAX(LEN(Werkingsgebied)) as MaxLength 
FROM Werkingsgebieden;



ALTER TABLE Werkingsgebieden
ALTER COLUMN Werkingsgebied nvarchar(500);


CREATE TABLE Werkingsgebieden (
	UUID uniqueidentifier DEFAULT newid() NOT NULL,
	ID int DEFAULT NEXT VALUE FOR [seq_Werkingsgebieden] NOT NULL,
	Werkingsgebied nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	SHAPE geometry NOT NULL,
	symbol nvarchar(265) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Begin_Geldigheid datetime NOT NULL,
	Eind_Geldigheid datetime NOT NULL,
	Created_By uniqueidentifier NOT NULL,
	Created_Date datetime NOT NULL,
	Modified_By uniqueidentifier NOT NULL,
	Modified_Date datetime NOT NULL,
	CONSTRAINT PK_Werkingsgebieden PRIMARY KEY (UUID),
	CONSTRAINT FK_Werkingsgebieden_Created_By FOREIGN KEY (Created_By) REFERENCES Gebruikers(UUID),
	CONSTRAINT FK_Werkingsgebieden_Modified_By FOREIGN KEY (Modified_By) REFERENCES Gebruikers(UUID)
);
CREATE INDEX FDO_Shape ON Werkingsgebieden (SHAPE);




--------------------------------------
-- ON PROD


ALTER TABLE Gebruikers ALTER COLUMN Wachtwoord nvarchar(500);
ALTER TABLE Werkingsgebieden ALTER COLUMN Werkingsgebied nvarchar(500);



--------------------------------------------
-- ON NEW


CREATE SEQUENCE seq_Gebruikers
    AS INT
    START WITH 1000
    INCREMENT BY 1;


CREATE TABLE Gebruikers (
	ID int DEFAULT NEXT VALUE FOR [seq_Gebruikers] NOT NULL,
	UUID uniqueidentifier DEFAULT newid() NOT NULL,
	Gebruikersnaam nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Wachtwoord nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Rol nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Email nvarchar(265) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'Actief' NULL,
	CONSTRAINT PK_Gebruikers PRIMARY KEY (UUID)
);



CREATE SEQUENCE seq_Werkingsgebieden
    AS INT
    START WITH 100
    INCREMENT BY 1;

CREATE TABLE Werkingsgebieden (
	UUID uniqueidentifier DEFAULT newid() NOT NULL,
	ID int DEFAULT NEXT VALUE FOR [seq_Werkingsgebieden] NOT NULL,
	Werkingsgebied nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SHAPE geometry NOT NULL,
	symbol nvarchar(265) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Begin_Geldigheid datetime NULL,
	Eind_Geldigheid datetime NULL,
	Created_By uniqueidentifier NOT NULL,
	Created_Date datetime NOT NULL,
	Modified_By uniqueidentifier NOT NULL,
	Modified_Date datetime NOT NULL,
	CONSTRAINT PK_Werkingsgebieden PRIMARY KEY (UUID)
);

ALTER TABLE Werkingsgebieden ADD CONSTRAINT FK_Werkingsgebieden_Created_By FOREIGN KEY (Created_By) REFERENCES Gebruikers(UUID);
ALTER TABLE Werkingsgebieden ADD CONSTRAINT FK_Werkingsgebieden_Modified_By FOREIGN KEY (Modified_By) REFERENCES Gebruikers(UUID);
