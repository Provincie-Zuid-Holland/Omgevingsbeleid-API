# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from passlib.hash import bcrypt
from faker.factory import Factory as FakerFactory
import uuid

import Api.Models
from Api.settings import null_uuid


class FixtureLoader():
    def __init__(self, db):
        self._db = db
        self._s = db.session

        fake = FakerFactory.create()
        fake.seed(0)

        self._fake = fake

        # Dict from `key` (not UUID) to the model
        # Can be used for associations etc
        self._instances = {}

    
    def load_fixtures(self):
        self._gebruiker("geb:null", UUID=null_uuid, Status="Inactief", Gebruikersnaam="Null", Email="null@example.com")
        self._gebruiker("geb:admin", Gebruikersnaam="Admin", Rol="Admin", Email="admin@example.com")
        self._gebruiker("geb:alex", Gebruikersnaam="Alex", Rol="Behandelend Ambtenaar", Email="alex@example.com")
        self._gebruiker("geb:fred", Gebruikersnaam="Frederik", Rol="Portefeuillehouder", Email="fred@example.com")

        self._ambitie("amb:1", Created_By="geb:admin")
        self._ambitie("amb:2", Created_By="geb:alex", Modified_By="geb:alex")

        self._beleidskeuzes("bel:1", Created_By="geb:fred")
        self._beleidskeuzes_ambities("bel:1", "amb:1", "Test omschrijving")

        self._s.commit()
        

    def _gebruiker(self, key, **kwargs):
        kwargs["Wachtwoord"] = bcrypt.hash(kwargs.get("Wachtwoord", "password"))

        if not "UUID" in kwargs:
            kwargs["UUID"] = uuid.uuid4()

        if not "Rol" in kwargs:
            kwargs["Rol"] = ""

        if not "Email" in kwargs:
            kwargs["Email"] = self._fake.ascii_safe_email()

        gebruiker = Api.Models.gebruikers.Gebruikers(**kwargs)

        self._instances[key] = gebruiker
        self._s.add(gebruiker)
        

    def _ambitie(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join([self._fake.paragraph(nb_sentences=10) for x in range(5)])

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        ambitie = Api.Models.ambities.Ambities(**kwargs)

        self._instances[key] = ambitie
        self._s.add(ambitie)
        

    def _beleidskeuzes(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving_Keuze" in kwargs:
            kwargs["Omschrijving_Keuze"] = "\n\n".join([self._fake.paragraph(nb_sentences=3) for x in range(2)])

        if not "Omschrijving_Werking" in kwargs:
            kwargs["Omschrijving_Werking"] = "\n\n".join([self._fake.paragraph(nb_sentences=10) for x in range(5)])

        if not "Provinciaal_Belang" in kwargs:
            kwargs["Provinciaal_Belang"] = "\n\n".join([self._fake.paragraph(nb_sentences=2) for x in range(2)])

        if not "Aanleiding" in kwargs:
            kwargs["Aanleiding"] = self._fake.paragraph(nb_sentences=4)

        if not "Status" in kwargs:
            kwargs["Status"] = "Actief"

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        ambitie = Api.Models.beleidskeuzes.Beleidskeuzes(**kwargs)

        self._instances[key] = ambitie
        self._s.add(ambitie)


    def _beleidskeuzes_ambities(self, beleidskeuze_key, ambitie_key, omschrijving):
        beleidskeuze = self._instances[beleidskeuze_key]
        ambitie = self._instances[ambitie_key]

        association = Api.Models.ambities.Beleidskeuze_Ambities(
            Koppeling_Omschrijving=omschrijving,
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Ambitie_UUID=ambitie.UUID
        )

        self._s.add(association)


    def _resolve_base_fields(self, **kwargs):

        if not "UUID" in kwargs:
            kwargs["UUID"] = uuid.uuid4()
        
        if not "Begin_Geldigheid" in kwargs:
            kwargs["Begin_Geldigheid"] = self._fake.date_time_between(start_date="-3y", end_date="-30d")
        
        if not "Eind_Geldigheid" in kwargs:
            kwargs["Eind_Geldigheid"] = self._fake.date_time_between(start_date="+30d", end_date="+3y")

        if not "Created_Date" in kwargs:
            kwargs["Created_Date"] = self._fake.date_time_between(start_date="-100d", end_date="-2d")
        
        if not "Modified_Date" in kwargs:
            kwargs["Modified_Date"] = kwargs["Created_Date"]
        
        # If we do have a Created_By then we expect it to be a key reference
        # So we have to resolve it to the model
        if "Created_By" in kwargs:
            kwargs["Created_By"] = self._instances[kwargs["Created_By"]].UUID
        else:
            # If we don't have a Created_By then we will use the null user
            kwargs["Created_By"] = null_uuid
   
        if "Modified_By" in kwargs:
            kwargs["Modified_By"] = self._instances[kwargs["Modified_By"]].UUID
        else:
            kwargs["Modified_By"] = null_uuid

        return kwargs
