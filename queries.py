"""
Query file voor alle endpoints. 
"""

# Queries voor Ambitie

# Alle actuele ambities selecteren
alle_ambities = 'SELECT * FROM Actuele_Ambities'

# Een ambitie selecteren op `uuid`
# Argumenten: uuid
ambitie_op_uuid = 'SELECT * FROM Ambities WHERE UUID=:uuid' 

# Een ambitie aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!

ambitie_aanmaken = '''
        INSERT INTO Ambities (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een ambitie aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
#        ID
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Modified_By,
#        Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
ambitie_aanpassen = '''
        INSERT INTO Ambities (ID, Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Queries voor Beleidsregels

# Alle actuele beleidsregels selecteren
alle_beleidsregels = 'SELECT * FROM Actuele_BeleidsRegels'

# Een beleidsregel selecteren op 'uuid'
# Argumenten: uuid
beleidsregel_op_uuid = 'SELECT * FROM BeleidsRegels WHERE UUID=:uuid'

# Een beleidsregel aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
beleidsregel_aanmaken = '''
        INSERT INTO BeleidsRegels (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een ambitie aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
#        ID
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Modified_By,
#        Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
beleidsregel_aanpassen = '''
        INSERT INTO BeleidsRegels (ID, Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Queries voor Doelen

# Alle actuele doel selecteren
alle_doelen = 'SELECT * FROM Actuele_Doelen'

# Een doel selecteren op 'uuid'
# Argumenten: uuid
doel_op_uuid = 'SELECT * FROM Doelen WHERE UUID=:uuid'

# Een doel aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
doel_aanmaken = '''
        INSERT INTO Doelen (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een doel aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
#        ID
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Modified_By,
#        Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
doel_aanpassen = '''
        INSERT INTO Doelen (ID, Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''



# Queries voor ProvincialeBelangen

# Alle actuele provenciaal belang selecteren
alle_provincialebelangen = 'SELECT * FROM Actuele_ProvincialeBelangen'

# Een provenciaal belang selecteren op 'uuid'
# Argumenten: uuid
provinciaalbelang_op_uuid = 'SELECT * FROM ProvincialeBelangen WHERE UUID=:uuid'

# Een provenciaal belang aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
provinciaalbelang_aanmaken = '''
        INSERT INTO ProvincialeBelangen (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een provenciaal belang aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
#        ID
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Modified_By,
#        Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
provinciaalbelang_aanpassen = '''
        INSERT INTO ProvincialeBelangen (ID, Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Queries voor Opgaven

# Alle actuele doel selecteren
alle_opgaven = 'SELECT * FROM Actuele_Opgaven'

# Een doel selecteren op 'uuid'
# Argumenten: uuid
opgave_op_uuid = 'SELECT * FROM Opgaven WHERE UUID=:uuid'

# Een opgave aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Weblink
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
opgave_aanmaken = '''
        INSERT INTO Opgaven (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''
# Een opgave aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
#        ID
#        Titel,
#        Omschrijving,
#        Weblink,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Modified_By,
#        Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
opgave_aanpassen = '''
        INSERT INTO Opgaven (ID, Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?); 
        '''
 
# Queries voor Themas

# Alle actuele thema's belang selecteren
alle_themas = 'SELECT * FROM Actuele_Themas'

# Een thema selecteren op 'uuid'
# Argumenten: uuid
thema_op_uuid = 'SELECT * FROM Themas WHERE UUID=:uuid'

# Een thema aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
thema_aanmaken = '''
        INSERT INTO Themas (Titel, Omschrijving, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een provenciaal belang aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
#        ID
#        Titel,
#        Omschrijving,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Modified_By,
#        Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
thema_aanpassen = '''
        INSERT INTO Themas (ID, Titel, Omschrijving, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''
# Queries voor BeleidsBeslissingen

# Alle actuele beleidsbeslissingen selecteren
alle_beleidsbeslissingen = 'SELECT * FROM Actuele_Beleidsbeslissingen'

# Een provenciaal belang selecteren op 'uuid'
# Argumenten: uuid
beleidsbeslissing_op_uuid = 'SELECT * FROM Beleidsbeslissingen WHERE UUID=:uuid'

# Een provenciaal belang aanmaken via een insert
# Argumenten: 
#        Titel,
#        Omschrijving,
#        Begin_Geldigheid,
#        Eind_Geldigheid,
#        Created_By,
#        Created_Date,
#        Created_By,
#        Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
beleidsbeslissing_aanmaken = '''
        INSERT INTO Beleidsbeslissingen (
            Eigenaar_1,
            Eigenaar_2,
            Status,
            Titel,
            Omschrijving_Keuze,
            Omschrijving_Werking,
            Motivering,
            Aanleiding,
            Afweging,
            Verordening_Realisatie,
            Begin_Geldigheid,
            Eind_Geldigheid,
            Created_By,
            Created_Date,
            Modified_By,
            Modified_Date
        )
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ? , ?, ?, ?, ? ,? ,?);
        '''

# Alle omgevinsbeleid objecten bij een beleidsbeslissing verkrijgen
# Alleen de relaties teruggeven
# Argumenten: uuid (van beleidsbeslissing)
omgevingsbeleid_bij_beleidsbeslissing = '''SELECT 
                                            fk_WerkingsGebieden,
                                            fk_Verordening,
                                            fk_Maatregelen,
                                            fk_BeleidsRegels,
                                            fk_Themas,
                                            fk_Ambities,
                                            fk_Doelen,
                                            fk_ProvincialeBelangen,
                                            fk_Opgaven,
                                            WerkingsGebieden_Omschrijving,
                                            Verordening_Omschrijving,
                                            Maatregelen_Omschrijving,
                                            BeleidsRegels_Omschrijving,
                                            Themas_Omschrijving,
                                            Ambities_Omschrijving,
                                            Doelen_Omschrijving,
                                            ProvincialeBelangen_Omschrijving,
                                            Opgaven_Omschrijving 
                                        FROM Omgevingsbeleid 
                                        WHERE fk_Beleidsbeslissingen = :uuid'''


omgevingsbeleid_aanmaken = '''
        INSERT INTO Omgevingsbeleid (
            fk_Beleidsbeslissingen,
            fk_WerkingsGebieden,
            fk_Verordening,
            fk_Maatregelen,
            fk_BeleidsRegels,
            fk_Themas,
            fk_Ambities,
            fk_Doelen,
            fk_ProvincialeBelangen,
            fk_Opgaven,
            WerkingsGebieden_Omschrijving,
            Verordening_Omschrijving,
            Maatregelen_Omschrijving,
            BeleidsRegels_Omschrijving,
            Themas_Omschrijving,
            Ambities_Omschrijving,
            Doelen_Omschrijving,
            ProvincialeBelangen_Omschrijving,
            Opgaven_Omschrijving,
            Eind_Geldigheid,
            Begin_Geldigheid,
            Modified_By,
            Modified_Date,
            Created_By,
            Created_Date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
'''

# Queries voor Maatregelen

# Alle actuele maatregelen selecteren
alle_maatregelen = 'SELECT * FROM Actuele_Maatregelen'

# Een maatregel selecteren op `uuid`
# Argumenten: uuid
maatregel_op_uuid = 'SELECT * FROM Maatregelen WHERE UUID=:uuid' 

# Een maatregel aanmaken via een insert
# Argumenten: 
       # Titel,
       # Motivering,
       # Beleids_Document
       # Gebied
       # Verplicht_Programma
       # Specifiek_Of_Generiek
       # Weblink,
       # Begin_Geldigheid,
       # Eind_Geldigheid,
       # Created_By,
       # Created_Date,
       # Created_By,
       # Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
 
maatregel_aanmaken = '''
        INSERT INTO Maatregelen (Titel, Motivering, Beleids_Document, fk_Gebied, Verplicht_Programma, Specifiek_Of_Generiek, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een maatregel aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
       # ID
       # Titel
       # Motivering
       # Beleids_Document
       # Gebied
       # Verplicht_Programma
       # Specifiek_Of_Generiek
       # Weblink
       # Begin_Geldigheid
       # Eind_Geldigheid
       # Created_By
       # Created_Date
       # Modified_By
       # Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!

maatregel_aanpassen = '''
        INSERT INTO Maatregelen
        (ID, Titel, Motivering, Beleids_Document, fk_Gebied, Verplicht_Programma, Specifiek_Of_Generiek, Weblink, Begin_Geldigheid, 
        Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Queries voor Verordening

# Alle actuele verordeningen selecteren
alle_verordeningen = 'SELECT * FROM Actuele_Verordeningen'

# Een verordening selecteren op `uuid`
# Argumenten: uuid
verordening_op_uuid = 'SELECT * FROM Verordeningen WHERE UUID=:uuid' 

# Een verordening aanmaken via een insert
# Argumenten: 
       # Titel ,
       # Omschrijving ,
       # Status ,
       # Type ,
       # Volgnummer ,
       # Werkingsgebied,
       # Begin_Geldigheid ,
       # Eind_Geldigheid ,
       # Created_By ,
       # Created_Date ,
       # Created_By ,
       # Created_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
        
verordening_aanmaken = '''
        INSERT INTO Verordeningen (Titel, Omschrijving, Status, Type, Volgnummer, fk_WerkingsGebied, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een verordening aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
       # ID,
       # Titel ,
       # Omschrijving ,
       # Status ,
       # Type ,
       # Volgnummer ,
       # Werkingsgebied,
       # Begin_Geldigheid ,
       # Eind_Geldigheid ,
       # Created_By ,
       # Created_Date ,
       # Modified_By ,
       # Mofified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!

verordening_aanpassen = '''
        INSERT INTO Verordeningen
        (ID, Titel, Omschrijving, Status, Type, Volgnummer, fk_WerkingsGebied, 
         Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Queries voor Werkingsgebieden

# Alle beschikbare werkingsgebieden selecteren
alle_werkingsgebieden = '''
SELECT [UUID]
      ,[OBJECTID]
      ,[Werkingsgebied]
      ,[Onderverdeling]
      ,[PRIMA]
      ,[FID]
      ,[Begin_Geldigheid]
      ,[Eind_Geldigheid]
      ,[Created_By]
      ,[Created_Date]
      ,[Modified_By]
      ,[Modified_Date]
  FROM [PZH_db].[dbo].[WerkingsGebieden]'''

# Een werkingsgebied selecteren op `uuid`
# Argumenten: uuid
werkingsgebied_op_uuid = '''
SELECT [UUID]
      ,[OBJECTID]
      ,[Werkingsgebied]
      ,[Onderverdeling]
      ,[PRIMA]
      ,[FID]
      ,[Begin_Geldigheid]
      ,[Eind_Geldigheid]
      ,[Created_By]
      ,[Created_Date]
      ,[Modified_By]
      ,[Modified_Date]
  FROM [PZH_db].[dbo].[WerkingsGebieden]
  WHERE UUID=:uuid
  '''

# Queries voor Geothemas

# Alle beschikbare geothemas selecteren
alle_geothemas = '''
SELECT [UUID]
      ,[Titel]
      ,[Omschrijving]
      ,[Begin_Geldigheid]
      ,[Eind_Geldigheid]
      ,[Created_By]
      ,[Created_Date]
      ,[Modified_By]
      ,[Modified_Date]
  FROM [PZH_db].[dbo].[GeoThemas]'''

# Een werkingsgebied selecteren op `uuid`
# Argumenten: uuid
geothema_op_uuid = '''
SELECT [UUID]
      ,[Titel]
      ,[Omschrijving]
      ,[Begin_Geldigheid]
      ,[Eind_Geldigheid]
      ,[Created_By]
      ,[Created_Date]
      ,[Modified_By]
      ,[Modified_Date]
  FROM [PZH_db].[dbo].[GeoThemas]
  WHERE UUID=:uuid
  '''

# Queries voor BeleidsRelaties

# Alle actuele beleidsrelaties selecteren
alle_beleidsrelaties = 'SELECT * FROM Actuele_BeleidsRelaties'

# Een verordening selecteren op `uuid`
# Argumenten: uuid
beleidsrelatie_op_uuid = 'SELECT * FROM BeleidsRelaties WHERE UUID=:uuid' 

# Een beleidsrelatie aanmaken via een insert
# Argumenten: 
       # Van_Beleidsbeslissing ,
       # Naar_Beleidsbeslissing ,
       # Omschrijving ,
       # Status ,
       # Aanvraag_Datum ,
       # Datum_Akkoord,
       # Begin_Geldigheid ,
       # Eind_Geldigheid ,
       # Created_By ,
       # Created_Date ,
       # Modified_By ,
       # Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
        
beleidsrelatie_aanmaken = '''
        INSERT INTO BeleidsRelaties (
           Van_Beleidsbeslissing ,
           Naar_Beleidsbeslissing ,
           Omschrijving ,
           Status ,
           Aanvraag_Datum ,
           Datum_Akkoord,
           Begin_Geldigheid ,
           Eind_Geldigheid ,
           Created_By ,
           Created_Date ,
           Modified_By ,
           Modified_Date
        )
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''
# Checken of een beleidsrelatie al bestaat tussen twee beleidsbeslissingen
# (Named) Argumenten:
    # bb1_UUID
    # bb2_UUID
    # bb1_UUID
    # bb2_UUID
    
check_beleidsrelatie = '''
    SELECT 
       UUID
      ,Van_Beleidsbeslissing
      ,Naar_Beleidsbeslissing
  FROM Actuele_BeleidsRelaties
  WHERE (Van_Beleidsbeslissing=?
  AND Naar_Beleidsbeslissing=?)
  OR (Naar_Beleidsbeslissing=?
    AND Van_Beleidsbeslissing=?);
'''
        
        
# Een beleidsrelatie aanpassen via een insert (we maken altijd een kopie)
# Argumenten: 
       # ID,
       # Van_Beleidsbeslissing ,
       # Naar_Beleidsbeslissing ,
       # Omschrijving ,
       # Status ,
       # Aanvraag_Datum ,
       # Datum_Akkoord,
       # Begin_Geldigheid ,
       # Eind_Geldigheid ,
       # Created_By ,
       # Created_Date ,
       # Modified_By ,
       # Modified_Date
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
beleidsrelatie_aanpassen = '''
        INSERT INTO BeleidsRelaties (
           ID,
           Van_Beleidsbeslissing ,
           Naar_Beleidsbeslissing ,
           Omschrijving ,
           Status ,
           Aanvraag_Datum ,
           Datum_Akkoord,
           Begin_Geldigheid ,
           Eind_Geldigheid ,
           Created_By ,
           Created_Date ,
           Modified_By ,
           Modified_Date
        )
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''

# Een beleidsrelatie selecteren op van/naar `uuid`
# Argumenten: uuid
beleidsrelatie_op_van_uuid = 'SELECT * FROM BeleidsRelaties WHERE Van_Beleidsbeslissing=:uuid' 
beleidsrelatie_op_naar_uuid = 'SELECT * FROM BeleidsRelaties WHERE Naar_Beleidsbeslissing=:uuid' 


# Queries voor Gebruikers

# Alle gebruikers selecteren
alle_gebruikers = 'SELECT * FROM Gebruikers'

# Een verordening selecteren op `uuid`
# Argumenten: uuid
gebruiker_op_uuid = 'SELECT * FROM Gebruikers WHERE UUID=:uuid' 

# Een gebruiker aanmaken via een insert
# Argumenten: 
       # Gebruikersnaam
       # Rol
       # Email
# !Argumenten worden als vraagtekens ontvangen!
# !OUTPUT inserted.UUID is verplicht!
        
gebruiker_aanmaken = '''
        INSERT INTO Gebruikers (Gebruikersnaam, Rol, Email)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?);
        '''

# Een gebruiker aanpassen via een update
# Argumenten: 
       # Gebruikersnaam,
       # Rol,
       # Email,
       # UUID
# !Argumenten worden als vraagtekens ontvangen!

gebruiker_aanpassen = '''
        UPDATE Gebruikers
        SET Gebruikersnaam=?, Rol=?, Email=?
        WHERE UUID=?
        '''






