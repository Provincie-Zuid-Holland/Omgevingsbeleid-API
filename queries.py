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
                                            fk_BeleidsRelaties,
                                            fk_Verordening,
                                            fk_Maatregelen,
                                            fk_BeleidsRegels,
                                            fk_Themas,
                                            fk_Ambities,
                                            fk_Doelen,
                                            fk_ProvincialeBelangen,
                                            fk_Opgaven,
                                            WerkingsGebieden_Omschrijving,
                                            BeleidsRelaties_Omschrijving,
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
            fk_BeleidsRelaties,
            fk_Verordening,
            fk_Maatregelen,
            fk_BeleidsRegels,
            fk_Themas,
            fk_Ambities,
            fk_Doelen,
            fk_ProvincialeBelangen,
            fk_Opgaven,
            WerkingsGebieden_Omschrijving,
            BeleidsRelaties_Omschrijving,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
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
















