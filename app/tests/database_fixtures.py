import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.core.utils.utils import DATE_FORMAT
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.db.tables import ObjectsTable
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide
from app.extensions.areas.db.tables import AreasTable
from app.extensions.areas.repository.mssql_area_geometry_repository import MssqlAreaGeometryRepository
from app.extensions.areas.repository.sqlite_area_geometry_repository import SqliteAreaGeometryRepository  # # noqa
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import ModuleObjectActionFilter, ModuleStatusCode, ModuleStatusCodeInternal
from app.extensions.relations.db.tables import RelationsTable
from app.extensions.source_werkingsgebieden.repository.mssql_geometry_repository import MssqlGeometryRepository
from app.extensions.source_werkingsgebieden.repository.sqlite_geometry_repository import SqliteGeometryRepository
from app.extensions.users.db import UsersTable
from app.extensions.users.db.tables import IS_ACTIVE
from app.tests.database_fixtures_publications import DatabaseFixturesPublications


class DatabaseFixtures:
    def __init__(self, db: Session):
        self._db = db
        self._geometry_repository = self._create_geometry_repository()
        self._area_geometry_repository = self._create_area_geometry_repository()

    def _create_geometry_repository(self):
        match self._db.bind.dialect.name:
            case "mssql":
                return MssqlGeometryRepository(self._db)
            case "sqlite":
                return SqliteGeometryRepository(self._db)
            case _:
                raise RuntimeError("Unknown database type connected")

    def _create_area_geometry_repository(self):
        match self._db.bind.dialect.name:
            case "mssql":
                return MssqlAreaGeometryRepository(self._db)
            case "sqlite":
                return SqliteAreaGeometryRepository(self._db)
            case _:
                raise RuntimeError("Unknown database type connected")

    def create_all(self):
        self.create_users()
        self.create_source_werkingsgebieden()
        self.create_areas()
        self.create_assets()
        self.create_object_statics()
        self.existing_objects()
        self.create_modules()
        self.create_relations()
        self.create_acknowledged_relations()
        self.create_visie()

        self.create_publication_templates()

    def create_publication_templates(self):
        publication_fixtures = DatabaseFixturesPublications(self._db)
        publication_fixtures.create_all()

    def create_users(self):
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Gebruikersnaam="Anton",
                Email="test@example.com",
                Rol="Superuser",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
                Gebruikersnaam="Bert",
                Email="b@example.com",
                Rol="Ambtelijk opdrachtgever",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000003"),
                Gebruikersnaam="Cees",
                Email="c@example.com",
                Rol="Behandelend Ambtenaar",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000004"),
                Gebruikersnaam="Daniel",
                Email="d@example.com",
                Rol="Beheerder",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000005"),
                Gebruikersnaam="Emma",
                Email="e@example.com",
                Rol="Portefeuillehouder",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000006"),
                Gebruikersnaam="Fred",
                Email="f@example.com",
                Rol="Test runner",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            UsersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000007"),
                Gebruikersnaam="Gerald",
                Email="g@example.com",
                Rol="Tester",
                Status=IS_ACTIVE,
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.commit()

    def create_source_werkingsgebieden(self):
        self._geometry_repository.add_werkingsgebied(
            uuidx=uuid.UUID("00000000-0009-0000-0000-000000000001"),
            idx=1,
            title="Maatwerkgebied glastuinbouw",
            text_shape="POLYGON ((74567.347600001842 443493.91890000325, 74608.622699998392 443619.86080000486, 74661.431899998352 443796.90439999942, 74657.325500000254 443794.78040000005, 74664.067999999956 443810.51300000178, 74729.171500001146 444013.33940000291, 74754.307000000073 444217.06900000118, 74766.111800000086 444287.24220000062, 74700.32570000003 444274.74290000094, 74617.775499999538 444246.9616000005, 74514.7938000001 444196.70150000026, 74448.482099998742 444165.69250000105, 74333.605200000064 444112.87550000072, 74204.86380000037 444067.32080000057, 74148.195700000957 444071.55770000169, 74232.0122999996 443919.14220000163, 74294.7186000012 443819.92320000188, 74402.363600000725 443672.54520000424, 74411.650600001187 443659.83020000259, 74518.027399998187 443515.38720000343, 74567.347600001842 443493.91890000325))",
            gml="""<gml:MultiSurface xmlns:gml="http://www.opengis.net/gml/3.2" srsName="_Netherlands-RDNew-2008_0" srsDimension="2"><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>92761.869 470790.261 92563.593 470616.166 92360.66 470815.519 92556.648 471030.144 92580.085 471015.423 92626.001 470963.642 92702.754 470877.085 92761.869 470790.261</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>93352.85 476533.177 93437.985 476585.022 93593.17 476382.088 93503.663 476313.572 93336.975 476514.656 93352.85 476533.177</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>97768.2 473177.881 97695.968 472945.709 97489.154 473082.299 97516.147 473091.296 97522.815 473099.869 97527.42 473114.436 97522.315 473138.915 97520.18 473164.511 97533.097 473218.024 97552.263 473287.353 97579.345 473335.393 97607.26 473370.287 97639.726 473398.599 97673.253 473414.139 97759.281 473414.234 97768.2 473177.881</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>95250.089 471275.614 95076.878 471092.912 94907.053 471256.473 94959.195 471256.473 95000.909 471273.853 95028.718 471303.401 95075.646 471379.876 95117.36 471414.637 95250.089 471275.614</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember></gml:MultiSurface>""",
            symbol="ES227",
            created_date=datetime(2023, 2, 2, 2, 2, 2),
            modified_date=datetime(2023, 2, 2, 2, 2, 2),
            start_validity=datetime(2023, 2, 2, 2, 2, 2),
            end_validity=datetime(2099, 2, 2, 2, 2, 2),
        )
        self._db.commit()

    def create_areas(self):
        self._area_geometry_repository.create_area(
            uuidx=uuid.UUID("00000000-0009-0000-0001-000000000001"),
            created_date=datetime(2023, 2, 2, 2, 2, 2),
            created_by_uuid=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            werkingsgebied={
                "UUID": "00000000-0009-0000-0000-000000000001",
                "ID": 1,
                "Title": "Maatwerkgebied glastuinbouw",
                "Symbol": "ES227",
                "Geometry": "POLYGON ((74567.347600001842 443493.91890000325, 74608.622699998392 443619.86080000486, 74661.431899998352 443796.90439999942, 74657.325500000254 443794.78040000005, 74664.067999999956 443810.51300000178, 74729.171500001146 444013.33940000291, 74754.307000000073 444217.06900000118, 74766.111800000086 444287.24220000062, 74700.32570000003 444274.74290000094, 74617.775499999538 444246.9616000005, 74514.7938000001 444196.70150000026, 74448.482099998742 444165.69250000105, 74333.605200000064 444112.87550000072, 74204.86380000037 444067.32080000057, 74148.195700000957 444071.55770000169, 74232.0122999996 443919.14220000163, 74294.7186000012 443819.92320000188, 74402.363600000725 443672.54520000424, 74411.650600001187 443659.83020000259, 74518.027399998187 443515.38720000343, 74567.347600001842 443493.91890000325))",
                "GML": """<gml:MultiSurface xmlns:gml="http://www.opengis.net/gml/3.2" srsName="_Netherlands-RDNew-2008_0" srsDimension="2"><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>92761.869 470790.261 92563.593 470616.166 92360.66 470815.519 92556.648 471030.144 92580.085 471015.423 92626.001 470963.642 92702.754 470877.085 92761.869 470790.261</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>93352.85 476533.177 93437.985 476585.022 93593.17 476382.088 93503.663 476313.572 93336.975 476514.656 93352.85 476533.177</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>97768.2 473177.881 97695.968 472945.709 97489.154 473082.299 97516.147 473091.296 97522.815 473099.869 97527.42 473114.436 97522.315 473138.915 97520.18 473164.511 97533.097 473218.024 97552.263 473287.353 97579.345 473335.393 97607.26 473370.287 97639.726 473398.599 97673.253 473414.139 97759.281 473414.234 97768.2 473177.881</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember><gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>95250.089 471275.614 95076.878 471092.912 94907.053 471256.473 94959.195 471256.473 95000.909 471273.853 95028.718 471303.401 95075.646 471379.876 95117.36 471414.637 95250.089 471275.614</gml:posList></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember></gml:MultiSurface>""",
                "Start_Validity": datetime(2023, 2, 2, 2, 2, 2).strftime(DATE_FORMAT)[:23],
                "End_Validity": datetime(2099, 2, 2, 2, 2, 2).strftime(DATE_FORMAT)[:23],
                "Created_Date": datetime(2023, 2, 2, 2, 2, 2).strftime(DATE_FORMAT)[:23],
                "Modified_Date": datetime(2023, 2, 2, 2, 2, 2).strftime(DATE_FORMAT)[:23],
            },
        )
        self._db.commit()

    def create_assets(self):
        self._db.add(
            AssetsTable(
                UUID=uuid.UUID("00000000-AAAA-0000-0000-000000000001"),
                Created_Date=datetime(2023, 2, 2, 2, 2, 2),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Lookup="bc4a2da2f2",
                Hash="bc4a2da2f2c63c52597e1bfe2d2df7f13a71abaed04a7b70aaff8b4c0fc62bc3",
                Meta=json.dumps({"ext": "png", "width": 302, "height": 100, "size": 26630}),
                Content="data:image/png;base64,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MWYtODEwNS1mMzgzZjdlNDRjOWIiCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6NGVkNmZjYzUtNDMzZS00OTJjLTg5ZjQtYjM3ZjI5NWM1YmJlIgogICB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6ZmIwMGNmNzAtMjQ1Yy00OGFmLWJiNTQtNjI2NDYxOGFiNmRhIgogICBkYzpGb3JtYXQ9ImltYWdlL3BuZyIKICAgR0lNUDpBUEk9IjIuMCIKICAgR0lNUDpQbGF0Zm9ybT0iTGludXgiCiAgIEdJTVA6VGltZVN0YW1wPSIxNzAwNDgxODg0MDI1NTI4IgogICBHSU1QOlZlcnNpb249IjIuMTAuMjgiCiAgIHRpZmY6T3JpZW50YXRpb249IjEiCiAgIHhtcDpDcmVhdG9yVG9vbD0iR0lNUCAyLjEwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6NWE0YmQ5ZDUtODQ5NS00ZDQ3LWI3YjMtOWUyMjAxYTEzMmMwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyMy0xMS0yMFQxMzowNDo0NCswMTowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg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",
            )
        )

    def create_object_statics(self):
        self._db.add(
            ObjectStaticsTable(
                Object_Type="ambitie",
                Object_ID=1,
                Code="ambitie-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Cached_Title="Titel van ambitie 1",
            )
        )
        self._db.add(
            ObjectStaticsTable(
                Object_Type="ambitie",
                Object_ID=2,
                Code="ambitie-2",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )
        self._db.add(
            ObjectStaticsTable(
                Object_Type="ambitie",
                Object_ID=3,
                Code="ambitie-3",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )

        self._db.add(
            ObjectStaticsTable(
                Object_Type="beleidsdoel",
                Object_ID=1,
                Code="beleidsdoel-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Cached_Title="Titel van beleidsdoel 1",
            )
        )
        self._db.add(
            ObjectStaticsTable(
                Object_Type="beleidsdoel",
                Object_ID=2,
                Code="beleidsdoel-2",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )

        self._db.add(
            ObjectStaticsTable(
                Object_Type="beleidskeuze",
                Object_ID=1,
                Code="beleidskeuze-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.add(
            ObjectStaticsTable(
                Object_Type="beleidskeuze",
                Object_ID=2,
                Code="beleidskeuze-2",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )

        self._db.add(
            ObjectStaticsTable(
                Object_Type="maatregel",
                Object_ID=1,
                Code="maatregel-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.add(
            ObjectStaticsTable(
                Object_Type="maatregel",
                Object_ID=2,
                Code="maatregel-2",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )

        self._db.add(
            ObjectStaticsTable(
                Object_Type="werkingsgebied",
                Object_ID=1,
                Code="werkingsgebied-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )
        self._db.commit()

    def existing_objects(self):
        self._db.add(
            ObjectsTable(
                Object_Type="ambitie",
                Object_ID=1,
                Code="ambitie-1",
                UUID=uuid.UUID("00000000-0000-0001-0000-A00000000001"),
                Title="Titel van de eerste ambitie",
                Description="<p>Description of Ambitie 1</p>",
                Created_Date=datetime(2022, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2022, 2, 2, 3, 3, 3),
                Start_Validity=datetime(2022, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.add(
            ObjectsTable(
                Object_Type="ambitie",
                Object_ID=3,
                Code="ambitie-3",
                UUID=uuid.UUID("00000000-0000-0001-0000-A00000000003"),
                Title="Titel van de derde ambitie",
                Description="<p>Description of Ambitie 3</p>",
                Created_Date=datetime(2022, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2022, 2, 2, 3, 3, 3),
                Start_Validity=datetime(2022, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()

    def create_modules(self):
        module: ModuleTable = ModuleTable(
            Module_ID=1,
            Title="Fixture module A",
            Description="Description of fixture module A",
            Module_Manager_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            Created_Date=datetime(2023, 2, 2, 2, 2, 2),
            Modified_Date=datetime(2023, 2, 2, 2, 2, 2),
            Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            Activated=1,
            Closed=0,
            Successful=0,
            Temporary_Locked=0,
        )
        module.status_history.append(
            ModuleStatusHistoryTable(
                Status=ModuleStatusCodeInternal.Niet_Actief,
                Created_Date=datetime(2023, 2, 2, 2, 2, 2),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        module.status_history.append(
            ModuleStatusHistoryTable(
                Status=ModuleStatusCode.Vastgesteld,
                Created_Date=datetime(2023, 2, 3, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.add(module)
        self._db.commit()

        # Ambitie
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="ambitie",
                Object_ID=1,
                Code="ambitie-1",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="ambitie",
                Object_ID=1,
                Code="ambitie-1",
                UUID=uuid.UUID("00000000-0000-0001-0000-000000000001"),
                Title="Titel van de eerste ambitie - edited",
                Description="<p>Description of Ambitie 1</p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="ambitie",
                Object_ID=2,
                Code="ambitie-2",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Edit,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="ambitie",
                Object_ID=2,
                Code="ambitie-2",
                UUID=uuid.UUID("00000000-0000-0001-0000-000000000002"),
                Title="Titel van de tweede ambitie",
                Description="<p>Description of Ambitie 2</p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()

        # Beleidsdoel
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidsdoel",
                Object_ID=1,
                Code="beleidsdoel-1",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidsdoel",
                Object_ID=1,
                Code="beleidsdoel-1",
                UUID=uuid.UUID("00000000-0000-0002-0000-000000000001"),
                Title="Titel van het eerste beleidsdoel",
                Description="<p>Description of beleidsdoel 1</p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidsdoel",
                Object_ID=2,
                Code="beleidsdoel-2",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidsdoel",
                Object_ID=2,
                Code="beleidsdoel-2",
                UUID=uuid.UUID("00000000-0000-0002-0000-000000000002"),
                Title="Titel van het tweede beleidsdoel",
                Description="<p>Description of beleidsdoel 2</p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()

        # Beleidskeuze
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidskeuze",
                Object_ID=1,
                Code="beleidskeuze-1",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidskeuze",
                Object_ID=1,
                Code="beleidskeuze-1",
                Hierarchy_Code="beleidsdoel-1",
                Werkingsgebied_Code="werkingsgebied-1",
                UUID=uuid.UUID("00000000-0000-0003-0000-000000000001"),
                Title="Titel van het eerste beleidskeuze",
                Description='<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eleifend lobortis libero, sit amet vestibulum lorem molestie sed.</p><img src="[ASSET:00000000-AAAA-0000-0000-000000000001]"/><p>Cras felis mi, finibus eget dignissim id, pretium egestas elit. Cras sodales eleifend velit vel aliquet. Nulla dapibus sem at velit suscipit, at varius augue porttitor. Morbi tempor vel est id dictum. Donec ante eros, rutrum eu quam non, interdum tristique turpis. Donec odio ipsum, tincidunt ut dignissim vel, scelerisque ut ex. Sed sit amet molestie tellus. Vestibulum porta condimentum molestie. Praesent non facilisis nisi, in egestas mi.<p>',
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidskeuze",
                Object_ID=2,
                Code="beleidskeuze-2",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="beleidskeuze",
                Object_ID=2,
                Code="beleidskeuze-2",
                Hierarchy_Code="beleidsdoel-1",
                Werkingsgebied_Code="werkingsgebied-1",
                UUID=uuid.UUID("00000000-0000-0003-0000-000000000002"),
                Title="Titel van het tweede beleidskeuze",
                Description="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eleifend lobortis libero, sit amet vestibulum lorem molestie sed. Cras felis mi, finibus eget dignissim id, pretium egestas elit. Cras sodales eleifend velit vel aliquet. Nulla dapibus sem at velit suscipit, at varius augue porttitor. Morbi tempor vel est id dictum. Donec ante eros, rutrum eu quam non, interdum tristique turpis. Donec odio ipsum, tincidunt ut dignissim vel, scelerisque ut ex. Sed sit amet molestie tellus. Vestibulum porta condimentum molestie. Praesent non facilisis nisi, in egestas mi. \n\nCurabitur porta dolor libero, auctor laoreet magna imperdiet tempus. Mauris at metus sit amet urna malesuada bibendum. Nulla ut tortor ut justo venenatis luctus nec vitae purus. Aliquam eget arcu sed ligula feugiat auctor. Integer at commodo turpis, id cursus enim. Pellentesque mattis posuere libero ut volutpat. Sed sagittis magna ac neque aliquam, eget scelerisque erat efficitur. Vivamus at erat rhoncus metus venenatis laoreet. Aliquam at pharetra leo. Vestibulum metus purus, molestie vel iaculis quis, suscipit nec velit. Nunc finibus felis quis iaculis posuere.</p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()

        # Maatregel
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="maatregel",
                Object_ID=1,
                Code="maatregel-1",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="maatregel",
                Object_ID=1,
                Code="maatregel-1",
                Werkingsgebied_Code="werkingsgebied-1",
                UUID=uuid.UUID("00000000-0000-0004-0000-000000000001"),
                Title="Titel van de eerste maatregel",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="maatregel",
                Object_ID=2,
                Code="maatregel-2",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="maatregel",
                Object_ID=2,
                Code="maatregel-2",
                Werkingsgebied_Code="werkingsgebied-1",
                UUID=uuid.UUID("00000000-0000-0004-0000-000000000002"),
                Title="Titel van de tweede maatregel",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()

        # Werkingsgebied
        self._db.add(
            ModuleObjectContextTable(
                Module_ID=module.Module_ID,
                Object_Type="werkingsgebied",
                Object_ID=1,
                Code="werkingsgebied-1",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Original_Adjust_On=None,
                Action=ModuleObjectActionFilter.Create,
                Explanation="Deze wil ik toevoegen",
                Conclusion="Geen conclusie",
            )
        )
        self._db.commit()
        self._db.add(
            ModuleObjectsTable(
                Module_ID=module.Module_ID,
                Object_Type="werkingsgebied",
                Object_ID=1,
                Code="werkingsgebied-1",
                UUID=uuid.UUID("00000000-0000-0005-0000-000000000001"),
                Title="Titel van de eerste werkingsgbied",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Area_UUID=uuid.UUID("00000000-0009-0000-0001-000000000001"),
            )
        )
        self._db.commit()

    def create_relations(self):
        # Ambitie <-> Beleidsdoel
        a = RelationsTable(Description="Ambitie 1 <-> Beleidsdoel 1")
        a.set_codes("ambitie-1", "beleidsdoel-1")
        self._db.add(a)
        b = RelationsTable(Description="Ambitie 2 <-> Beleidsdoel 2")
        b.set_codes("ambitie-2", "beleidsdoel-2")
        self._db.add(b)

        # Beleidsdoel <-> Beleidskeuze
        c = RelationsTable(Description="Beleidsdoel 1 <-> Beleidskeuze 1")
        c.set_codes("beleidsdoel-1", "beleidskeuze-1")
        self._db.add(c)
        d = RelationsTable(Description="Beleidsdoel 2 <-> Beleidskeuze 2")
        d.set_codes("beleidsdoel-2", "beleidskeuze-2")
        self._db.add(d)

        # Beleidskeuze <-> Maatregel
        c = RelationsTable(Description="Beleidskeuze 1 <-> Maatregel 1")
        c.set_codes("beleidskeuze-1", "maatregel-1")
        self._db.add(c)
        d = RelationsTable(Description="Beleidskeuze 2 <-> Maatregel 2")
        d.set_codes("beleidskeuze-2", "maatregel-2")
        self._db.add(d)
        self._db.commit()

    def create_acknowledged_relations(self):
        ack_table: AcknowledgedRelationsTable = AcknowledgedRelationsTable(
            Requested_By_Code="beleidskeuze-1",
            Created_Date=datetime(2023, 2, 2, 3, 3, 3),
            Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            Modified_Date=datetime(2023, 2, 3, 3, 3, 3),
            Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
        )
        ack_table.with_sides(
            AcknowledgedRelationSide(
                Object_ID=1,
                Object_Type="beleidskeuze",
                Acknowledged=datetime(2023, 2, 2, 3, 3, 3),
                Acknowledged_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Explanation="Relatie naar beleidskeuze 2",
            ),
            AcknowledgedRelationSide(
                Object_ID=2,
                Object_Type="beleidskeuze",
                Acknowledged=datetime(2023, 2, 3, 3, 3, 3),
                Acknowledged_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Explanation="Relatie naar beleidskeuze 1",
            ),
        )
        self._db.add(ack_table)
        self._db.commit()

    def create_visie(self):
        self._db.add(
            ObjectStaticsTable(
                Object_Type="visie_algemeen",
                Object_ID=1,
                Code="visie_algemeen-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )
        self._db.commit()
        self._db.add(
            ObjectsTable(
                Object_Type="visie_algemeen",
                Object_ID=1,
                Code="visie_algemeen-1",
                UUID=uuid.UUID("00000000-0000-0010-0000-000000000001"),
                Title="Inleiding",
                Description="""
<h3>Leeswijzer</h3>
<p>De Zuid-Hollandse leefomgeving verbeteren, elke dag, dat is waar de provincie
aan werkt. Zeven vernieuwingsambities laten zien waar Zuid-Holland naartoe wil.
Noem het gerust uitdagingen. Met de zeven ambities maakt de provincie ruimte
voor belangrijke ontwikkelingen rond participatie, bereikbaarheid, energie,
economie, natuur, woningbouw en gezondheid en veiligheid. Wie vooral benieuwd
is naar de vergezichten en kansen gaat direct naar hoofdstuk 4 waar de ambities
op een rij staan. Dat hoofdstuk is de kern van dit document. Welke kaders en
uitgangspunten bij het werken aan die ambities gelden, staat beschreven in
hoofdstuk 5. Hoofdstuk 3 laat zien waar de provincie Zuid-Holland nu staat. De
sturingsfilosofie die de provincie gebruikt om, samen met partners, te groeien van
waar Zuid-Holland nu staat naar waar de provincie naartoe wil, is het onderwerp
van hoofdstuk 2. De wijze waarop ons beleid tot stand komt staat beschreven in
Hoofdstuk 6. De hoofdstukken 7 tot en met 8 ten slotte maken het beeld
compleet met een integraal overzicht van alle beleidsdoelen, beleidskeuzes en de
kaarten die op hoofdlijnen . Dit hoofdstuk is ook (actueel) te raadplegen via
https://omgevingsbeleid.zuid-holland.nl</p>

<h3>Doel en opzet</h3>
<p>De Omgevingsvisie van Zuid-Holland biedt een strategische blik op de lange(re)
termijn voor de gehele fysieke leefomgeving en bevat de hoofdzaken van het te
voeren integrale beleid van de provincie Zuid-Holland. De Omgevingsvisie vormt
samen met de Omgevingsverordening en het Omgevingsprogramma het
provinciale Omgevingsbeleid van de provincie Zuid-Holland. Het Omgevingsbeleid
beschrijft hoe de provincie werkt aan een goede leefomgeving, welke plannen
daarvoor zijn, welke regels daarbij gelden en welke inspanningen de provincie
daarvoor levert.</p>""",
                Start_Validity=datetime(2023, 2, 2, 3, 3, 3),
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )

        self._db.add(
            ObjectStaticsTable(
                Object_Type="visie_algemeen",
                Object_ID=2,
                Code="visie_algemeen-2",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )
        self._db.commit()
        self._db.add(
            ObjectsTable(
                Object_Type="visie_algemeen",
                Object_ID=2,
                Code="visie_algemeen-2",
                UUID=uuid.UUID("00000000-0000-0010-0000-000000000002"),
                Title="Sturingsfilosofie",
                Description="""
<h3>Ruimte voor ontwikkeling, met waarborg voor kwaliteit: 8 sturingsprincipes voor de fysieke leefomgeving</h3>
<p>De provincie Zuid-Holland heeft met haar uitgebreide instrumentarium grote
meerwaarde bij het oplossen van de maatschappelijke opgaven van vandaag en
morgen. En met inbreng van kennis en creativiteit vanuit de samenleving kan nog
meer worden bereikt. De kunst is het oplossend vermogen van de maatschappij
te stimuleren en te benutten. Alleen ga je sneller, samen kom je verder</p>

<h3>Doel en opzet</h3>
<p>Zuid-Holland biedt daarom ruimte en vertrouwen aan maatschappelijke
initiatieven. Maar ruimte en vrijheid gedijen alleen binnen grenzen. Daarom werkt
de provincie Zuid-Holland vanuit een aantal principes en kaders, voor haarzelf én
haar partners, als waarborg voor de kwaliteit van de fysieke leefomgeving.</p>""",
                Start_Validity=datetime(2023, 2, 2, 3, 3, 3),
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()

        self._db.add(
            ObjectStaticsTable(
                Object_Type="visie_algemeen",
                Object_ID=3,
                Code="visie_algemeen-3",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            )
        )
        self._db.commit()
        self._db.add(
            ObjectsTable(
                Object_Type="visie_algemeen",
                Object_ID=3,
                Code="visie_algemeen-3",
                UUID=uuid.UUID("00000000-0000-0010-0000-000000000003"),
                Title="Hier staat Zuid-Holland nu",
                Description="""
<p>De huidige staat van de leefomgeving van Zuid-Holland beschrijven we aan de
hand van twee onderdelen:</p>
<ul><li><p>Een beschrijving van de KWALITEITEN VAN ZUID-HOLLAND: de drie
deltalandschappen, de Zuid-Hollandse steden en de strategische ligging in
internationale netwerken.</p></li>
<li><p>Een beschrijving van de huidige staat van de LEEFOMGEVING op basis van de
leefomgevingstoets.</p></li></ul>

<h3>De kwaliteiten van Zuid-Holland</h3>
<p>Zuid-Holland is een strategisch gelegen, vruchtbare delta, grotendeels onder
zeeniveau. De wijze waarop de bewoners van deze delta door de eeuwen heen
het water hebben weten te bedwingen en benutten, heeft een landschap
opgeleverd waarvan de culturele waarde internationaal wordt erkend en dat
cruciale leefgebieden bevat voor internationaal beschermde plant- en
diersoorten. Zuid-Holland is uniek in de combinatie van het kust-, veen- en
rivierdeltalandschap. Deze zijn allemaal verbonden met grote waterstructuren: de
zee, rivieren en zeearmen. Ze hebben elk een eigen, kenmerkend samenspel
opgeleverd van bodem, water en grondgebruik, dat voortdurend in beweging is</p>""",
                Start_Validity=datetime(2023, 2, 2, 3, 3, 3),
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        self._db.commit()
