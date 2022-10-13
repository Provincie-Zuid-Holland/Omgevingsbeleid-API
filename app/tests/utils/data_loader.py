# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from passlib.hash import bcrypt
from faker.factory import Factory as FakerFactory
import uuid

from app.models import (
    Ambitie,
    Belang,
    Beleidsprestatie,
    Beleidskeuze,
    Beleidsmodule,
    Beleidsprestatie,
    Beleidsregel,
    Beleidsrelatie,
    Gebruiker,
    Maatregel,
    Thema,
    Verordening,
    Werkingsgebied,
    Beleidskeuze_Ambities,
    Beleidskeuze_Belangen,
    Beleidskeuze_Beleidsdoelen,
    Beleidskeuze_Maatregelen,
    Beleidskeuze_Werkingsgebieden,
    Beleidskeuze_Beleidsprestaties,
    Beleidsmodule_Maatregelen,
    Beleidsmodule_Beleidskeuzes,
    Beleidskeuze_Beleidsregels,
    Beleidskeuze_Themas,
    Beleidskeuze_Verordeningen,
)
from app.core.config import settings
from app.models.beleidsdoel import Beleidsdoel
from .test_shapes import pzh_shape


class FixtureLoader:
    def __init__(self, session):
        self._s = session

        fake = FakerFactory.create()
        fake.seed(0)

        self._fake = fake

        # Dict from `key` (not UUID) to the model
        # Can be used for associations etc
        self._instances = {}

    def load_fixtures(self):
        null_uuid = settings.NULL_UUID

        # Null models
        self._gebruiker(
            "geb:null",
            UUID=null_uuid,
            Status="Inactief",
            Gebruikersnaam="Null",
            Email="null@test.com",
        )
        self._ambitie("amb:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink="")
        self._belang("blg:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink="")
        self._beleidsdoel(
            "doe:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink=""
        )
        self._beleidskeuze(
            "keu:null",
            UUID=null_uuid,
            Titel="",
            Omschrijving_Keuze="",
            Omschrijving_Werking="",
            Provinciaal_Belang="",
            Aanleiding="",
            Status="",
            Weblink="",
        )
        self._beleidsrelatie("rla:null", UUID=null_uuid, Titel="", Omschrijving="")
        self._werkingsgebied("wgb:null", UUID=null_uuid, Werkingsgebied="", symbol="")
        self._maatregel(
            "maa:null",
            UUID=null_uuid,
            Titel="",
            Omschrijving="",
            Toelichting="",
            Toelichting_Raw="",
            Weblink="",
            Status="",
            Tags="",
        )
        self._beleidsmodule("mod:null", UUID=null_uuid, Titel="")
        self._beleidsprestatie(
            "pre:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink=""
        )
        self._beleidsregel(
            "rgl:null",
            UUID=null_uuid,
            Titel="",
            Omschrijving="",
            Weblink="",
            Externe_URL="",
        )
        self._thema("tma:null", UUID=null_uuid, Titel="", Omschrijving="", Weblink="")
        self._verordening(
            "ver:null",
            UUID=null_uuid,
            Titel="",
            Inhoud="",
            Weblink="",
            Status="",
            Type="",
            Volgnummer="",
        )

        # Gebruikers
        self._gebruiker(
            "geb:admin", Gebruikersnaam="Admin", Rol="Superuser", Email="admin@test.com"
        )
        self._gebruiker(
            "geb:alex",
            Gebruikersnaam="Alex",
            Rol="Behandelend Ambtenaar",
            Email="alex@test.com",
        )
        self._gebruiker(
            "geb:fred",
            Gebruikersnaam="Frederik",
            Rol="Portefeuillehouder",
            Email="fred@test.com",
        )
        self._gebruiker(
            "geb:beheerder-jan",
            Gebruikersnaam="Beheerder Jan",
            Rol="Beheerder",
            Email="beheerder@test.com",
        )

        # Api tests require that of each model at least one record exists
        self._ambitie("amb:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred")
        self._belang("blg:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred")
        self._beleidsdoel(
            "doe:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._beleidskeuze(
            "keu:1",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Uitgecheckt",
        )
        self._beleidsrelatie(
            "rla:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._werkingsgebied(
            "wgb:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._maatregel(
            "maa:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._beleidsmodule(
            "mod:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._beleidsprestatie(
            "pre:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._beleidsregel(
            "rgl:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )
        self._thema("tma:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred")
        self._verordening(
            "ver:1", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred"
        )

        # These ambities are expected to exist for tests using `Tests.TestUtils.schema_data.reference_rich_beleidskeuze`
        self._ambitie(
            "amb:rrb1",
            UUID="B786487C-3E65-4DD8-B360-D2C56BF83172",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
        )
        self._ambitie(
            "amb:rrb2",
            UUID="0254A475-08A6-4B2A-A455-96BA6BE70A19",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
        )

        # Used in Tests.test_api
        self._beleidskeuze(
            "keu:3",
            UUID="82448A0A-989B-11EC-B909-0242AC120002",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="UsedForFiltering",
            Titel="Title Used For Filtering",
        )
        self._beleidskeuze(
            "keu:4",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Ontwerp PS",
            Titel="First",
        )
        self._beleidskeuze(
            "keu:5",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Ontwerp PS",
            Titel="Second",
        )
        self._beleidskeuze(
            "keu:6",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Vigerend",
            Titel="Second",
        )

        self._beleidskeuze(
            "keu:7",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Ontwerp PS",
            Afweging="Test4325123$%",
            Titel="Test4325123$%",
        )
        self._beleidskeuze(
            "keu:8",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Ontwerp GS",
            Afweging="Test4325123$%",
            Titel="Anders",
        )
        self._beleidskeuze(
            "keu:9",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Vigerend",
            Afweging="Anders",
            Titel="Test4325123$%",
        )

        self._beleidskeuze(
            "keu:10",
            UUID="94A45F78-98A9-11EC-B909-0242AC120002",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Vigerend",
            Titel="Will be modified",
        )
        self._beleidsprestatie(
            "pre:2",
            UUID="B5f7C134-98AD-11EC-B909-0242AC120002",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Titel="Will be modified",
        )

        # Werkingsgebieden which are assigned to beleidskeuzes and maatregelen
        self._werkingsgebied(
            "wgb:2",
            ID=1000,
            UUID="8EB1ED00-0002-1111-0000-000000000000",
            Werkingsgebied="Not the newest of its version",
            Created_Date="2022-01-01T10:00:00",
        )
        self._beleidskeuzes_werkingsgebieden("keu:10", "wgb:2")
        self._werkingsgebied(
            "wgb:2b",
            ID=1000,
            UUID="8EB1ED00-0002-2222-0000-000000000000",
            Werkingsgebied="Valid as it it joined with active beleidskeuze",
            Created_Date="2022-02-02T10:00:00",
        )
        self._beleidskeuzes_werkingsgebieden("keu:10", "wgb:2b")

        self._werkingsgebied(
            "wgb:3",
            UUID="8EB1ED00-0003-0000-0000-000000000000",
            Werkingsgebied="Valid as it is joined with active maatregel",
        )
        self._maatregel(
            "maa:2",
            UUID="38909E6A-98AC-11EC-B909-0242AC120002",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Status="Vigerend",
            Titel="Will be modified",
            Gebied_UUID="wgb:3",
        )

        self._werkingsgebied(
            "wgb:4",
            UUID="8EB1ED00-0004-0000-0000-000000000000",
            Werkingsgebied="Invalid as it is joined with wrong maatregel Status",
        )
        self._maatregel(
            "maa:3",
            Status="Test",
            Gebied_UUID="wgb:4",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
        )

        self._werkingsgebied(
            "wgb:5",
            UUID="8EB1ED00-0005-0000-0000-000000000000",
            Werkingsgebied="Invalid as the maatregel has the wrong status",
        )
        self._maatregel(
            "maa:4",
            Status="Test",
            Gebied_UUID="wgb:5",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Begin_Geldigheid="1991-11-23T10:00:00",
            Eind_Geldigheid="1992-11-23T10:00:00",
        )

        self._werkingsgebied(
            "wgb:6",
            UUID="8EB1ED00-0006-0000-0000-000000000000",
            Werkingsgebied="All_Valid but not Valid as the Eind_Geldingheid of this werkingsgebied is expired",
            Begin_Geldigheid="1991-11-23T10:00:00",
            Eind_Geldigheid="1992-11-23T10:00:00",
        )
        self._beleidskeuzes_werkingsgebieden("keu:10", "wgb:6")

        self._werkingsgebied(
            "wgb:7",
            UUID="8EB1ED00-0007-0000-0000-000000000000",
            Werkingsgebied="All_Valid but not Valid as the Begin_Geldingheid of this werkingsgebied is in the future",
            Begin_Geldigheid="9991-11-23T10:00:00",
            Eind_Geldigheid="9992-11-23T10:00:00",
        )
        self._beleidskeuzes_werkingsgebieden("keu:10", "wgb:7")

        # Werkingsgebied with the shape of the Provincie Zuid Holland, in order to test geo features
        self._werkingsgebied(
            "wgb:pzh",
            Werkingsgebied="Shape of the provincie Zuid Holland",
            SHAPE=pzh_shape,
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Begin_Geldigheid="1991-11-23T10:00:00",
            Eind_Geldigheid="1992-11-23T10:00:00",
        )

        # Beleidskeuze which has a mutation with Status=Vigerend, but is still in the future
        self._beleidskeuze(
            "keu:11",
            ID=1011,
            UUID="FEC2E000-0011-0011-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-01T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Ontwerp GS Concept",
            Titel="Versie 1 in Ontwerp GS Concept - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:12",
            ID=1011,
            UUID="FEC2E000-0011-0012-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-02T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Ontwerp GS",
            Titel="Versie 1 Ontwerp GS - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:13",
            ID=1011,
            UUID="FEC2E000-0011-0013-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-03T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Ontwerp in inspraak",
            Titel="Versie 1 Ontwerp in inspraak - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:14",
            ID=1011,
            UUID="FEC2E000-0011-0014-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-04T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Definitief ontwerp GS concept",
            Titel="Versie 1 Definitief ontwerp GS concept - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:15",
            ID=1011,
            UUID="FEC2E000-0011-0015-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-05T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Definitief ontwerp GS",
            Titel="Versie 1 Definitief ontwerp GS - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:16",
            ID=1011,
            UUID="FEC2E000-0011-0016-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-06T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Vastgesteld",
            Titel="Versie 1 Vastgesteld - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:17",
            ID=1011,
            UUID="FEC2E000-0011-0017-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-07T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Vigerend",
            Titel="Versie 1 Vigerend - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )

        self._beleidskeuze(
            "keu:18",
            ID=1011,
            UUID="FEC2E000-0011-0021-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-01-01T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Ontwerp GS Concept",
            Titel="Versie 2 in Ontwerp GS Concept - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:19",
            ID=1011,
            UUID="FEC2E000-0011-0022-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-02-02T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Ontwerp GS",
            Titel="Versie 2 Ontwerp GS - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:20",
            ID=1011,
            UUID="FEC2E000-0011-0023-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-02-03T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Ontwerp in inspraak",
            Titel="Versie 2 Ontwerp in inspraak - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:21",
            ID=1011,
            UUID="FEC2E000-0011-0024-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-02-04T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Definitief ontwerp GS concept",
            Titel="Versie 2 Definitief ontwerp GS concept - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:22",
            ID=1011,
            UUID="FEC2E000-0011-0025-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-02-05T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Definitief ontwerp GS",
            Titel="Versie 2 Definitief ontwerp GS - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:23",
            ID=1011,
            UUID="FEC2E000-0011-0026-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-02-06T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Vastgesteld",
            Titel="Versie 2 Vastgesteld - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:24",
            ID=1011,
            UUID="FEC2E000-0011-0027-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-01-01T10:00:00",
            Modified_Date="2020-02-07T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Vigerend",
            Titel="Versie 2 Vigerend - datum is tegenwoordig",
            Afweging="beleidskeuze1011",
            Begin_Geldigheid="2120-01-01T10:00:00",
            Eind_Geldigheid="9999-01-01T10:00:00",
        )

        # Beleidskeuze which gets "removed" because a new version is set to the past
        self._beleidskeuze(
            "keu:30",
            ID=1030,
            UUID="FEC2E000-1030-0001-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-02-01T10:00:00",
            Modified_Date="2020-02-01T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Vigerend",
            Titel="Versie 1 Vigerend en in de huidige tijd",
            Afweging="beleidskeuze1030",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2120-01-01T10:00:00",
        )
        self._beleidskeuze(
            "keu:31",
            ID=1030,
            UUID="FEC2E000-1030-0002-0000-000000000000",
            Created_By_UUID="geb:admin",
            Created_Date="2020-02-01T10:00:00",
            Modified_Date="2020-03-01T10:00:00",
            Modified_By_UUID="geb:admin",
            Status="Vigerend",
            Titel="Versie 2 Vigerend maar in het verleden",
            Afweging="beleidskeuze1030",
            Begin_Geldigheid="2020-01-01T10:00:00",
            Eind_Geldigheid="2021-01-01T10:00:00",
        )

        #
        self._ambitie("amb:2", Created_By_UUID="geb:admin")
        self._ambitie("amb:3", Created_By_UUID="geb:alex", Modified_By_UUID="geb:alex")

        self._beleidskeuze("keu:2", Created_By_UUID="geb:fred")
        self._beleidskeuzes_ambities("keu:2", "amb:2", "Test omschrijving")

        # "Water" related models mainly used in search tests
        self._ambitie(
            "amb:water",
            Created_By_UUID="geb:alex",
            Modified_By_UUID="geb:alex",
            Titel="Geen overstromingen in Den Haag",
            Omschrijving="We willen water beter begeleiden zodat we geen overstromingen meer hebben.",
        )
        self._beleidsdoel(
            "doe:water",
            Created_By_UUID="geb:alex",
            Modified_By_UUID="geb:alex",
            Titel="Leven met water",
            Omschrijving="De provincie wil Zuid-Holland beschermen tegen wateroverlast en overstromingen en de gevolgen van eventuele overstromingen zoveel mogelijk beperken. Deze opgave wordt groter door de effecten van klimaatverandering (zeespiegelstijging en toenemende extreme neerslag), bodemdaling en toenemende druk op de beschikbare ruimte.",
        )

        self._beleidskeuze("keu:water", Created_By_UUID="geb:alex")
        self._beleidskeuzes_ambities("keu:water", "amb:water")
        self._beleidskeuzes_beleidsdoelen("keu:water", "doe:water")

        self._maatregel(
            "maa:dijk",
            Titel="Hogere dijken gaan ons redden",
            Omschrijving="We gaan meer geld steken in het bouwen van hogere dijken",
        )
        self._beleidskeuzes_maatregelen("keu:water", "maa:dijk")

        for i in range(30):
            self._beleidskeuze(
                f"keu:water-{i}", Titel=f"{i} - Test informatie voor zoeken naar water"
            )

        # Verordeningsobject that are linked to beleidskeuzes
        self._verordening(
            "ver:2", Created_By_UUID="geb:fred", Modified_By_UUID="geb:fred", Type="Lid"
        )
        self._verordening(
            "ver:3",
            Created_By_UUID="geb:fred",
            Modified_By_UUID="geb:fred",
            Type="Artikel",
        )
        self._beleidskeuzes_verordeningen("keu:6", "ver:2")
        self._beleidskeuzes_verordeningen("keu:6", "ver:3")

        self._s.commit()

    def _gebruiker(self, key, **kwargs):
        kwargs["Wachtwoord"] = bcrypt.hash(kwargs.get("Wachtwoord", "password"))

        if not "UUID" in kwargs:
            kwargs["UUID"] = uuid.uuid4()

        if not "Rol" in kwargs:
            kwargs["Rol"] = ""

        if not "Email" in kwargs:
            kwargs["Email"] = self._fake.ascii_safe_email()

        model = Gebruiker(**kwargs)
        self._add(key, model)

    def _ambitie(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        model = Ambitie(**kwargs)
        self._add(key, model)

    def _belang(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        if not "Type" in kwargs:
            kwargs["Type"] = self._fake.random_element(
                elements=("Nationaal Belang", "Wettelijk Taak & Bevoegdheid")
            )

        model = Belang(**kwargs)
        self._add(key, model)

    def _beleidskeuze(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving_Keuze" in kwargs:
            kwargs["Omschrijving_Keuze"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=3) for x in range(2)]
            )

        if not "Omschrijving_Werking" in kwargs:
            kwargs["Omschrijving_Werking"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Provinciaal_Belang" in kwargs:
            kwargs["Provinciaal_Belang"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=2) for x in range(2)]
            )

        if not "Afweging" in kwargs:
            kwargs["Afweging"] = self._fake.paragraph(nb_sentences=4)

        if not "Aanleiding" in kwargs:
            kwargs["Aanleiding"] = self._fake.paragraph(nb_sentences=4)
        if not "Status" in kwargs:
            kwargs["Status"] = "Vigerend"

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        model = Beleidskeuze(**kwargs)
        self._add(key, model)

    def _beleidsmodule(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Besluit_Datum" in kwargs:
            kwargs["Besluit_Datum"] = self._fake.date_time_between(
                start_date="-300d", end_date="-100d"
            )

        model = Beleidsmodule(**kwargs)
        self._add(key, model)

    def _beleidsdoel(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        model = Beleidsdoel(**kwargs)
        self._add(key, model)

    def _beleidsrelatie(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=3)[:45]

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Status" in kwargs:
            kwargs["Status"] = "Vigerend"

        if not "Aanvraag_Datum" in kwargs:
            kwargs["Aanvraag_Datum"] = self._fake.date_time_between(
                start_date="-300d", end_date="-200d"
            )

        if not "Datum_Akkoord" in kwargs:
            kwargs["Datum_Akkoord"] = self._fake.date_time_between(
                start_date="-100d", end_date="-20d"
            )

        if "Van_Beleidskeuze_UUID" in kwargs:
            kwargs["Van_Beleidskeuze_UUID"] = self._instances[
                kwargs["Van_Beleidskeuze_UUID"]
            ].UUID
        else:
            kwargs["Van_Beleidskeuze_UUID"] = settings.NULL_UUID

        if "Naar_Beleidskeuze_UUID" in kwargs:
            kwargs["Naar_Beleidskeuze_UUID"] = self._instances[
                kwargs["Naar_Beleidskeuze_UUID"]
            ].UUID
        else:
            kwargs["Naar_Beleidskeuze_UUID"] = settings.NULL_UUID

        model = Beleidsrelatie(**kwargs)
        self._add(key, model)

    def _beleidsprestatie(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        model = Beleidsprestatie(**kwargs)
        self._add(key, model)

    def _beleidsregel(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        if not "Externe_URL" in kwargs:
            kwargs["Externe_URL"] = self._fake.uri()

        model = Beleidsregel(**kwargs)
        self._add(key, model)

    def _thema(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        model = Thema(**kwargs)
        self._add(key, model)

    def _maatregel(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Omschrijving" in kwargs:
            kwargs["Omschrijving"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Toelichting" in kwargs:
            kwargs["Toelichting"] = self._fake.sentence(nb_words=20)

        if not "Toelichting_Raw" in kwargs:
            kwargs["Toelichting_Raw"] = self._fake.sentence(nb_words=8)

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        if "Gebied_UUID" in kwargs:
            kwargs["Gebied_UUID"] = self._instances[kwargs["Gebied_UUID"]].UUID
        else:
            kwargs["Gebied_UUID"] = settings.NULL_UUID

        if not "Status" in kwargs:
            kwargs["Status"] = "Vigerend"

        if not "Gebied_Duiding" in kwargs:
            kwargs["Gebied_Duiding"] = "Indicatief"

        if not "Tags" in kwargs:
            kwargs["Tags"] = ""

        if "Aanpassing_Op_UUID" in kwargs:
            kwargs["Aanpassing_Op_UUID"] = self._instances[
                kwargs["Aanpassing_Op_UUID"]
            ].UUID
        else:
            kwargs["Aanpassing_Op_UUID"] = settings.NULL_UUID

        if "Eigenaar_1_UUID" in kwargs:
            kwargs["Eigenaar_1_UUID"] = self._instances[kwargs["Eigenaar_1_UUID"]].UUID
        else:
            kwargs["Eigenaar_1_UUID"] = settings.NULL_UUID

        if "Eigenaar_2_UUID" in kwargs:
            kwargs["Eigenaar_2_UUID"] = self._instances[kwargs["Eigenaar_2_UUID"]].UUID
        else:
            kwargs["Eigenaar_2_UUID"] = settings.NULL_UUID

        if "Portefeuillehouder_1_UUID" in kwargs:
            kwargs["Portefeuillehouder_1_UUID"] = self._instances[
                kwargs["Portefeuillehouder_1_UUID"]
            ].UUID
        else:
            kwargs["Portefeuillehouder_1_UUID"] = settings.NULL_UUID

        if "Portefeuillehouder_2_UUID" in kwargs:
            kwargs["Portefeuillehouder_2_UUID"] = self._instances[
                kwargs["Portefeuillehouder_2_UUID"]
            ].UUID
        else:
            kwargs["Portefeuillehouder_2_UUID"] = settings.NULL_UUID

        if "Opdrachtgever_UUID" in kwargs:
            kwargs["Opdrachtgever_UUID"] = self._instances[
                kwargs["Opdrachtgever_UUID"]
            ].UUID
        else:
            kwargs["Opdrachtgever_UUID"] = settings.NULL_UUID

        model = Maatregel(**kwargs)
        self._add(key, model)

    def _verordening(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Titel" in kwargs:
            kwargs["Titel"] = self._fake.sentence(nb_words=10)

        if not "Inhoud" in kwargs:
            kwargs["Inhoud"] = "\n\n".join(
                [self._fake.paragraph(nb_sentences=10) for x in range(5)]
            )

        if not "Weblink" in kwargs:
            kwargs["Weblink"] = self._fake.uri()

        if not "Status" in kwargs:
            kwargs["Status"] = "Vigerend"

        if not "Type" in kwargs:
            kwargs["Type"] = self._fake.random_element(
                elements=("Hoofdstuk", "Artikel", "Afdeling")
            )

        if "Gebied_UUID" in kwargs:
            kwargs["Gebied_UUID"] = self._instances[kwargs["Gebied_UUID"]].UUID
        else:
            kwargs["Gebied_UUID"] = settings.NULL_UUID

        if not "Volgnummer" in kwargs:
            kwargs["Volgnummer"] = self._fake.bothify(text="????-########")

        if "Portefeuillehouder_1_UUID" in kwargs:
            kwargs["Portefeuillehouder_1_UUID"] = self._instances[
                kwargs["Portefeuillehouder_1_UUID"]
            ].UUID
        else:
            kwargs["Portefeuillehouder_1_UUID"] = settings.NULL_UUID

        if "Portefeuillehouder_2_UUID" in kwargs:
            kwargs["Portefeuillehouder_2_UUID"] = self._instances[
                kwargs["Portefeuillehouder_2_UUID"]
            ].UUID
        else:
            kwargs["Portefeuillehouder_2_UUID"] = settings.NULL_UUID

        if "Eigenaar_1_UUID" in kwargs:
            kwargs["Eigenaar_1_UUID"] = self._instances[kwargs["Eigenaar_1_UUID"]].UUID
        else:
            kwargs["Eigenaar_1_UUID"] = settings.NULL_UUID

        if "Eigenaar_2_UUID" in kwargs:
            kwargs["Eigenaar_2_UUID"] = self._instances[kwargs["Eigenaar_2_UUID"]].UUID
        else:
            kwargs["Eigenaar_2_UUID"] = settings.NULL_UUID

        if "Opdrachtgever_UUID" in kwargs:
            kwargs["Opdrachtgever_UUID"] = self._instances[
                kwargs["Opdrachtgever_UUID"]
            ].UUID
        else:
            kwargs["Opdrachtgever_UUID"] = settings.NULL_UUID

        model = Verordening(**kwargs)
        self._add(key, model)

    def _werkingsgebied(self, key, **kwargs):
        kwargs = self._resolve_base_fields(**kwargs)

        if not "Werkingsgebied" in kwargs:
            kwargs["Werkingsgebied"] = self._fake.sentence(nb_words=10)

        if not "symbol" in kwargs:
            kwargs["symbol"] = ""

        if not "SHAPE" in kwargs:
            kwargs["SHAPE"] = "POLYGON ((0 0, 150 0, 150 150, 0 150, 0 0))"

        model = Werkingsgebied(**kwargs)
        self._add(key, model)

    def _beleidskeuzes_ambities(self, beleidskeuze_key, ambitie_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        ambitie = self._instances[ambitie_key]
        association = Beleidskeuze_Ambities(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Ambitie_UUID=ambitie.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_belangen(self, beleidskeuze_key, belang_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        belang = self._instances[belang_key]
        association = Beleidskeuze_Belangen(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Belang_UUID=belang.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_beleidsdoelen(
        self, beleidskeuze_key, beleidsdoel_key, omschrijving=""
    ):
        beleidskeuze = self._instances[beleidskeuze_key]
        beleidsdoel = self._instances[beleidsdoel_key]
        association = Beleidskeuze_Beleidsdoelen(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Beleidsdoel_UUID=beleidsdoel.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_maatregelen(
        self, beleidskeuze_key, maatregel_key, omschrijving=""
    ):
        beleidskeuze = self._instances[beleidskeuze_key]
        maatregel = self._instances[maatregel_key]
        association = Beleidskeuze_Maatregelen(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Maatregel_UUID=maatregel.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_werkingsgebieden(
        self, beleidskeuze_key, werkingsgebied_key, omschrijving=""
    ):
        beleidskeuze = self._instances[beleidskeuze_key]
        werkingsgebied = self._instances[werkingsgebied_key]
        association = Beleidskeuze_Werkingsgebieden(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Werkingsgebied_UUID=werkingsgebied.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_beleidsprestaties(
        self, beleidskeuze_key, beleidsprestatie_key, omschrijving=""
    ):
        beleidskeuze = self._instances[beleidskeuze_key]
        beleidsprestatie = self._instances[beleidsprestatie_key]
        association = Beleidskeuze_Beleidsprestaties(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Beleidsprestatie_UUID=beleidsprestatie.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidsmodule_maatregelen(
        self, beleidsmodule_key, maatregel_key, omschrijving=""
    ):
        beleidsmodule = self._instances[beleidsmodule_key]
        maatregel = self._instances[maatregel_key]
        association = Beleidsmodule_Maatregelen(
            Beleidsmodule_UUID=beleidsmodule.UUID,
            Maatregel_UUID=maatregel.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidsmodule_beleidskeuzes(
        self, beleidsmodule_key, beleidskeuze_key, omschrijving=""
    ):
        beleidsmodule = self._instances[beleidsmodule_key]
        beleidskeuze = self._instances[beleidskeuze_key]
        association = Beleidsmodule_Beleidskeuzes(
            Beleidsmodule_UUID=beleidsmodule.UUID,
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_beleidsregels(
        self, beleidskeuze_key, beleidsregel_key, omschrijving=""
    ):
        beleidskeuze = self._instances[beleidskeuze_key]
        beleidsregel = self._instances[beleidsregel_key]
        association = Beleidskeuze_Beleidsregels(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Beleidsregel_UUID=beleidsregel.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_themas(self, beleidskeuze_key, thema_key, omschrijving=""):
        beleidskeuze = self._instances[beleidskeuze_key]
        thema = self._instances[thema_key]
        association = Beleidskeuze_Themas(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Thema_UUID=thema.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _beleidskeuzes_verordeningen(
        self, beleidskeuze_key, verordening_key, omschrijving=""
    ):
        beleidskeuze = self._instances[beleidskeuze_key]
        verordening = self._instances[verordening_key]
        association = Beleidskeuze_Verordeningen(
            Beleidskeuze_UUID=beleidskeuze.UUID,
            Verordening_UUID=verordening.UUID,
            Koppeling_Omschrijving=omschrijving,
        )
        self._s.add(association)

    def _resolve_base_fields(self, **kwargs):
        if not "UUID" in kwargs:
            kwargs["UUID"] = uuid.uuid4()

        if not "Begin_Geldigheid" in kwargs:
            kwargs["Begin_Geldigheid"] = self._fake.date_time_between(
                start_date="-3y", end_date="-30d"
            )

        if not "Eind_Geldigheid" in kwargs:
            kwargs["Eind_Geldigheid"] = self._fake.date_time_between(
                start_date="+30d", end_date="+3y"
            )

        if not "Created_Date" in kwargs:
            kwargs["Created_Date"] = self._fake.date_time_between(
                start_date="-100d", end_date="-2d"
            )

        if not "Modified_Date" in kwargs:
            kwargs["Modified_Date"] = kwargs["Created_Date"]

        # If we do have a Created_By then we expect it to be a key reference
        # So we have to resolve it to the model
        if "Created_By_UUID" in kwargs:
            kwargs["Created_By_UUID"] = self._instances[kwargs["Created_By_UUID"]].UUID
        else:
            # If we don't have a Created_By then we will use the null user
            kwargs["Created_By_UUID"] = settings.NULL_UUID

        if "Modified_By_UUID" in kwargs:
            kwargs["Modified_By_UUID"] = self._instances[
                kwargs["Modified_By_UUID"]
            ].UUID
        else:
            kwargs["Modified_By_UUID"] = settings.NULL_UUID

        return kwargs

    def _add(self, key, model):
        assert (
            not key in self._instances
        ), f"instance key '{key}' already exists, please use a different key"
        self._instances[key] = model
        self._s.add(model)
