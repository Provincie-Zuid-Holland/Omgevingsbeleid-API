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

# Queries voor Themas

# Alle actuele provenciaal belang selecteren
alle_themas = 'SELECT * FROM Actuele_Themas'

# Een provenciaal belang selecteren op 'uuid'
# Argumenten: uuid
thema_op_uuid = 'SELECT * FROM Themas WHERE UUID=:uuid'

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
