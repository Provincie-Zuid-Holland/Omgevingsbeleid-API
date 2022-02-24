# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from passlib.hash import bcrypt
from faker.factory import Factory as FakerFactory
import uuid
import pyodbc
import time

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
        # Null models
        self._gebruiker("geb:null", UUID=null_uuid, Status="Inactief", Gebruikersnaam="Null", Email="null@example.com")
        self._ambitie("amb:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink="")
        self._beleidsdoel("doe:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink="")
        self._beleidskeuzes("bel:null", UUID=null_uuid, Titel="", Omschrijving_Keuze="", Omschrijving_Werking="", Provinciaal_Belang="", Aanleiding="", Status="", Weblink="")
        self._werkingsgebieden("wgb:null", UUID=null_uuid, Werkingsgebied="", symbol="")
        self._maatregelen("maa:null", UUID=null_uuid, Titel="", Omschrijving="", Toelichting="", Toelichting_Raw="", Weblink="", Status="", Tags="")
        
        # Gebruikers
        self._gebruiker("geb:admin", Gebruikersnaam="Admin", Rol="Admin", Email="admin@example.com")
        self._gebruiker("geb:alex", Gebruikersnaam="Alex", Rol="Behandelend Ambtenaar", Email="alex@example.com")
        self._gebruiker("geb:fred", Gebruikersnaam="Frederik", Rol="Portefeuillehouder", Email="fred@example.com")

        self._ambitie("amb:1", Created_By="geb:admin")
        self._ambitie("amb:2", Created_By="geb:alex", Modified_By="geb:alex")

        self._beleidskeuzes("bel:1", Created_By="geb:fred")
        self._beleidskeuzes_ambities("bel:1", "amb:1", "Test omschrijving")

        # "Water" related models mainly used in search tests
        self._ambitie("amb:water", Created_By="geb:alex", Modified_By="geb:alex", Titel="Geen overstromingen in Den Haag", Omschrijving="We willen water beter begeleiden zodat we geen overstromingen meer hebben.")
        self._beleidsdoel("doe:water", Created_By="geb:alex", Modified_By="geb:alex", Titel="Leven met water", Omschrijving="De provincie wil Zuid-Holland beschermen tegen wateroverlast en overstromingen en de gevolgen van eventuele overstromingen zoveel mogelijk beperken. Deze opgave wordt groter door de effecten van klimaatverandering (zeespiegelstijging en toenemende extreme neerslag), bodemdaling en toenemende druk op de beschikbare ruimte.")

        self._beleidskeuzes("bel:water", Created_By="geb:alex")
        self._beleidskeuzes_ambities("bel:water", "amb:water")
        self._beleidskeuzes_beleidsdoelen("bel:water", "doe:water")
        
        self._maatregelen("maa:dijk", Titel="Hogere dijken gaan ons redden", Omschrijving="We gaan meer geld steken in het bouwen van hogere dijken")
        self._beleidskeuzes_maatregelen("bel:water", "maa:dijk")

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

        model = Api.Models.ambities.Ambities(**kwargs)
        self._instances[key] = model
        self._s.add(model)

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

        model = Api.Models.beleidskeuzes.Beleidskeuzes(**kwargs)
        self._instances[key] = model
        self._s.add(model)

    def _beleidsdoel(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join([self._fake.paragraph(nb_sentences=10) for x in range(5)])

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        model = Api.Models.beleidsdoelen.Beleidsdoelen(**kwargs)
        self._instances[key] = model
        self._s.add(model)

    def _maatregelen(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join([self._fake.paragraph(nb_sentences=10) for x in range(5)])

        if not "Toelichting" in kwargs:
            kwargs["Toelichting"] = self._fake.sentence(nb_words=20)

        if not "Toelichting_Raw" in kwargs:
            kwargs["Toelichting_Raw"] = self._fake.sentence(nb_words=8)

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        if "Gebied" in kwargs:
            kwargs["Gebied"] = self._instances[kwargs["Gebied"]].UUID
        else:
            kwargs["Gebied"] = null_uuid

        if not "Status" in kwargs:
            kwargs["Status"] = "Vigerend"

        if not "Gebied_Duiding" in kwargs:
            kwargs["Gebied_Duiding"] = "Indicatief"

        if not "Tags" in kwargs:
            kwargs["Tags"] = ""

        if "Aanpassing_Op" in kwargs:
            kwargs["Aanpassing_Op"] = self._instances[kwargs["Aanpassing_Op"]].UUID
        else:
            kwargs["Aanpassing_Op"] = null_uuid

        if "Eigenaar_1" in kwargs:
            kwargs["Eigenaar_1"] = self._instances[kwargs["Eigenaar_1"]].UUID
        else:
            kwargs["Eigenaar_1"] = null_uuid

        if "Eigenaar_2" in kwargs:
            kwargs["Eigenaar_2"] = self._instances[kwargs["Eigenaar_2"]].UUID
        else:
            kwargs["Eigenaar_2"] = null_uuid

        if "Portefeuillehouder_1" in kwargs:
            kwargs["Portefeuillehouder_1"] = self._instances[kwargs["Portefeuillehouder_1"]].UUID
        else:
            kwargs["Portefeuillehouder_1"] = null_uuid

        if "Portefeuillehouder_2" in kwargs:
            kwargs["Portefeuillehouder_2"] = self._instances[kwargs["Portefeuillehouder_2"]].UUID
        else:
            kwargs["Portefeuillehouder_2"] = null_uuid

        if "Opdrachtgever" in kwargs:
            kwargs["Opdrachtgever"] = self._instances[kwargs["Opdrachtgever"]].UUID
        else:
            kwargs["Opdrachtgever"] = null_uuid

        model = Api.Models.maatregelen.Maatregelen(**kwargs)
        self._instances[key] = model
        self._s.add(model)

    def _werkingsgebieden(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Werkingsgebied" in kwargs:
            kwargs["Werkingsgebied"] = self._fake.sentence(nb_words=10)

        if not "symbol" in kwargs:
            kwargs["symbol"] = ""

        if not "SHAPE" in kwargs:
            kwargs["SHAPE"] = "POLYGON ((0 0, 150 0, 150 150, 0 150, 0 0))"

        model = Api.Models.werkingsgebieden.Werkingsgebieden(**kwargs)
        self._instances[key] = model
        self._s.add(model)

    def _beleidskeuzes_ambities(self, beleidskeuze_key, ambitie_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        ambitie = self._instances[ambitie_key]
        association = Api.Models.ambities.Beleidskeuze_Ambities(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Ambitie_UUID=ambitie.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_beleidsdoelen(self, beleidskeuze_key, beleidsdoel_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        beleidsdoel = self._instances[beleidsdoel_key]
        association = Api.Models.beleidsdoelen.Beleidskeuze_Beleidsdoelen(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Beleidsdoel_UUID=beleidsdoel.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_maatregelen(self, beleidskeuze_key, maatregel_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        maatregel = self._instances[maatregel_key]
        association = Api.Models.maatregelen.Beleidskeuze_Maatregelen(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Maatregel_UUID=maatregel.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_werkingsgebieden(self, beleidskeuze_key, werkingsgebied_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        werkingsgebied = self._instances[werkingsgebied_key]
        association = Api.Models.werkingsgebieden.Beleidskeuze_Werkingsgebieden(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Werkingsgebied_UUID=werkingsgebied.UUID,
            Koppeling_Omschrijving=omschrijving,
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
