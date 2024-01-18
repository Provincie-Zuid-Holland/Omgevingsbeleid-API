import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.db.tables import ObjectsTable
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import ModuleObjectActionFilter, ModuleStatusCode, ModuleStatusCodeInternal
from app.extensions.relations.db.tables import RelationsTable
from app.extensions.users.db import UsersTable
from app.extensions.users.db.tables import IS_ACTIVE
from app.extensions.werkingsgebieden.repository.mssql_geometry_repository import MssqlGeometryRepository
from app.extensions.werkingsgebieden.repository.sqlite_geometry_repository import SqliteGeometryRepository


class DatabaseFixtures:
    def __init__(self, db: Session):
        self._db = db
        self._geometry_repository = self._create_geometry_repository()

    def _create_geometry_repository(self):
        match self._db.bind.dialect.name:
            case "mssql":
                return MssqlGeometryRepository(self._db)
            case "sqlite":
                return SqliteGeometryRepository(self._db)
            case _:
                raise RuntimeError("Unknown database type connected")

    def create_all(self):
        self.create_users()
        self.create_werkingsgebieden()
        self.create_object_statics()
        self.existing_objects()
        self.create_modules()
        self.create_relations()
        self.create_acknowledged_relations()

        self.create_visie()

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

    def create_werkingsgebieden(self):
        # Werkingsgebied with 3 onderverdelingen
        self._geometry_repository.add_werkingsgebied(
            uuidx=uuid.UUID("00000000-0009-0000-0000-000000000001"),
            idx=1,
            title="Maatwerkgebied glastuinbouw",
            # This probably is not used in favor of onderverdelingen
            text_shape="POLYGON ((74567.347600001842 443493.91890000325, 74608.622699998392 443619.86080000486, 74661.431899998352 443796.90439999942, 74657.325500000254 443794.78040000005, 74664.067999999956 443810.51300000178, 74729.171500001146 444013.33940000291, 74754.307000000073 444217.06900000118, 74766.111800000086 444287.24220000062, 74700.32570000003 444274.74290000094, 74617.775499999538 444246.9616000005, 74514.7938000001 444196.70150000026, 74448.482099998742 444165.69250000105, 74333.605200000064 444112.87550000072, 74204.86380000037 444067.32080000057, 74148.195700000957 444071.55770000169, 74232.0122999996 443919.14220000163, 74294.7186000012 443819.92320000188, 74402.363600000725 443672.54520000424, 74411.650600001187 443659.83020000259, 74518.027399998187 443515.38720000343, 74567.347600001842 443493.91890000325))",
            created_date=datetime(2023, 2, 2, 2, 2, 2),
            modified_date=datetime(2023, 2, 2, 2, 2, 2),
            start_validity=datetime(2023, 2, 2, 2, 2, 2),
            end_validity=None,
        )
        self._geometry_repository.add_onderverdeling(
            uuidx=uuid.UUID("00000000-0009-0000-0000-100000000001"),
            idx=1,
            title="Maatwerkgebied glastuinbouw Greenport West-Holland",
            text_shape="POLYGON ((74567.347600001842 443493.91890000325, 74608.622699998392 443619.86080000486, 74661.431899998352 443796.90439999942, 74657.325500000254 443794.78040000005, 74664.067999999956 443810.51300000178, 74729.171500001146 444013.33940000291, 74754.307000000073 444217.06900000118, 74766.111800000086 444287.24220000062, 74700.32570000003 444274.74290000094, 74617.775499999538 444246.9616000005, 74514.7938000001 444196.70150000026, 74448.482099998742 444165.69250000105, 74333.605200000064 444112.87550000072, 74204.86380000037 444067.32080000057, 74148.195700000957 444071.55770000169, 74232.0122999996 443919.14220000163, 74294.7186000012 443819.92320000188, 74402.363600000725 443672.54520000424, 74411.650600001187 443659.83020000259, 74518.027399998187 443515.38720000343, 74567.347600001842 443493.91890000325))",
            symbol="AS117",
            werkingsgebied_title="Maatwerkgebied glastuinbouw",
            werkingsgebied_uuid=uuid.UUID("00000000-0009-0000-0000-000000000001"),
            created_date=datetime(2023, 2, 2, 2, 2, 2),
            modified_date=datetime(2023, 2, 2, 2, 2, 2),
            start_validity=datetime(2023, 2, 2, 2, 2, 2),
            end_validity=None,
        )
        self._geometry_repository.add_onderverdeling(
            uuidx=uuid.UUID("00000000-0009-0000-0000-100000000002"),
            idx=1,
            title="Maatwerkgebied glastuinbouw Greenport Aalsmeer",
            text_shape="MULTIPOLYGON (((110357.59760000178 467595.77320000017, 110263.98479999971 468030.81300000218, 110277.21400000164 468030.81300000282, 110249.4327000007 468173.68829999934, 110227.44310000172 468230.60850000114, 109984.8487999998 468180.30290000309, 110028.50510000062 467983.18790000089, 110156.44090000167 468008.91209999961, 110233.15920000151 467655.71819999965, 110304.99529999867 467606.1559000035, 110357.59760000178 467595.77320000017)), ((109993.14730000125 466422.40269999939, 110061.06089999905 466521.61290000204, 110168.35269999877 466696.81090000062, 110318.25589999928 466946.61120000115, 110498.50539999829 467237.24600000004, 110426.65920000158 467295.62100000161, 110387.28090000153 467465.39730000205, 110338.59739999846 467457.98889999971, 110326.95569999891 467425.18050000159, 110289.9140000008 467382.84710000135, 110193.60550000146 467275.95520000369, 110124.81370000169 467220.92179999885, 110048.61349999902 467139.43000000081, 109948.07160000128 467044.17979999975, 109868.69649999967 466953.16290000203, 109805.10500000051 466886.56400000083, 109741.35590000078 466828.127200002, 109632.1660000011 466727.17020000267, 109579.97289999943 466670.85669999785, 109625.7564999983 466619.73900000058, 109631.26359999923 466602.01310000056, 109636.5417999998 466589.69729999691, 109669.9701999985 466554.25820000138, 109715.46290000154 466505.74940000154, 109721.44359999895 466512.90400000085, 109772.88569999859 466560.11800000223, 109815.24540000045 466514.79770000005, 109865.22709999977 466560.82250000321, 109923.3482999988 466501.91590000171, 109993.14730000125 466422.40269999939)), ((110218.72329999885 466141.93120000511, 110270.31720000129 466148.54580000072, 110402.60909999907 466223.95220000175, 110605.04179999976 466335.04329999973, 110604.38439999895 466346.21960000211, 110599.09270000082 466404.42810000083, 110608.35310000181 466426.91770000226, 110646.71779999879 466486.44910000009, 110649.36360000077 466497.03240000381, 110695.6658000015 466575.08460000274, 110710.21790000054 466605.51180000097, 110686.40540000059 466628.00140000368, 110662.59279999882 466639.90769999841, 110629.51990000159 466659.75150000158, 110628.19689999893 466672.98070000281, 110636.13450000068 466687.53280000109, 110640.03979999943 466696.12449999963, 110628.82829999924 466704.17190000106, 110561.35940000042 466741.21359999938, 110526.96350000051 466775.60949999781, 110489.92179999876 466800.74500000256, 110483.30719999968 466791.4844999974, 110222.13069999963 466371.2584000004, 110065.94819999865 466485.14350000222, 110013.98440000042 466401.56840000011, 110012.7126000002 466398.8513000026, 109980.93149999899 466352.52639999846, 109976.85720000041 466334.87080000166, 109962.75490000099 466309.87130000105, 109993.82699999961 466290.09810000006, 110034.83749999852 466258.34810000064, 110134.05649999905 466165.7437000043, 110169.77529999989 466148.54580000346, 110218.72329999885 466141.93120000511)), ((109226.93749999997 465808.5599000022, 109257.27459999919 465838.00480000296, 109336.64970000088 465893.5674000025, 109409.55290000141 465932.44910000049, 109443.11430000138 465945.08909999934, 109482.49989999831 465969.53530000371, 109527.1501000002 466007.33850000141, 109572.12939999999 466047.02600000263, 109615.50640000026 466079.15720000042, 109674.69269999868 466109.98340000137, 109725.58799999952 466126.40120000322, 109823.26940000059 466212.0865999994, 109827.51359999931 466216.30900000158, 109656.9805999994 466393.33850000007, 109626.04800000039 466367.28999999783, 109539.76229999957 466460.90190000291, 109567.43879999967 466490.20650000178, 109461.50189999864 466602.32470000308, 109420.22679999849 466565.01840000221, 109361.48919999975 466518.98080000124, 109332.91420000044 466495.16829999746, 109270.20780000086 466430.87440000015, 109185.80550000072 466351.63149999827, 109117.01370000097 466282.83969999978, 109025.07079999894 466204.12600000051, 108929.82070000096 466116.151900004, 108969.508200001 466073.81850000273, 109178.66180000082 465858.62360000151, 109226.93749999997 465808.5599000022)), ((109043.4354000017 465344.55739999982, 109213.68389999868 465347.79330000078, 109228.23600000143 465351.76199999993, 109265.27780000122 465351.76199999946, 109286.44449999928 465366.31410000211, 109345.97590000182 465412.61630000139, 109345.97590000182 465511.8352999973, 109355.23629999907 465554.16869999981, 109357.882100001 465577.98120000045, 109364.49669999999 465600.47080000339, 109434.61149999869 465603.11670000112, 109446.51770000163 465621.63760000328, 109448.31679999825 465638.08590000257, 109593.91279999912 465648.10489999957, 109600.71959999949 465656.7680999997, 109599.48200000077 465725.45480000065, 109858.84230000156 465740.90269999753, 109874.01460000125 465759.27229999891, 109871.6862999983 465778.95740000228, 109884.63929999992 465838.93100000231, 109877.32290000096 466000.91170000064, 109865.72150000183 466169.13180000155, 109846.53629999982 466193.72760000156, 109759.55730000141 466110.78029999905, 109728.23389999945 466094.65110000048, 109687.15260000156 466074.81879999943, 109661.77230000125 466068.67840000079, 109619.67049999913 466045.59030000208, 109595.22419999909 466029.29280000256, 109559.91299999879 466004.84660000115, 109536.82490000129 465980.400300002, 109492.75420000029 465935.90080000134, 109431.8999000006 465904.15069999988, 109373.69150000068 465885.62990000256, 109326.31560000032 465855.45290000056, 109276.06500000136 465813.35100000072, 109238.03750000152 465775.32350000157, 109201.71200000124 465721.5879000033, 109175.56379999963 465678.8966999987, 109147.04320000112 465615.06490000215, 109087.94090000178 465470.23320000275, 109071.28510000183 465431.71680000215, 109043.4354000017 465344.55739999982)))",
            symbol="AS118",
            werkingsgebied_title="Maatwerkgebied glastuinbouw",
            werkingsgebied_uuid=uuid.UUID("00000000-0009-0000-0000-000000000001"),
            created_date=datetime(2023, 2, 2, 2, 2, 2),
            modified_date=datetime(2023, 2, 2, 2, 2, 2),
            start_validity=datetime(2023, 2, 2, 2, 2, 2),
            end_validity=None,
        )
        self._geometry_repository.add_onderverdeling(
            uuidx=uuid.UUID("00000000-0009-0000-0000-100000000003"),
            idx=1,
            title="Maatwerkgebied glastuinbouw buiten Greenports",
            text_shape="POLYGON ((98660.359499998434 472113.99210000382, 98681.44810000062 472160.22690000158, 98778.687899999291 472604.43580000079, 98578.2232999988 472686.02000000182, 98413.122999999672 472751.37220000348, 98423.441799998269 472780.6087000008, 98311.655099999145 472828.76289999735, 98318.534299999475 472849.40049999912, 98067.444200001657 472914.7527000031, 97999.160999998479 472931.14080000215, 97969.76850000018 472938.19489999692, 97945.02239999926 472939.49740000261, 97921.209899999216 472948.75780000258, 97896.074400000274 472954.04950000095, 97872.261799998581 472936.85150000174, 97810.913100000485 472894.0067000027, 97824.14229999861 472868.87120000029, 97836.29300000146 472828.33300000289, 97832.745900001391 472794.04460000107, 97783.086800001562 472641.52019999956, 97750.171399999424 472534.29330000113, 97737.108800001457 472497.70899999974, 98105.903000000835 472343.1862999982, 98119.259899999946 472334.28159999946, 98660.359499998434 472113.99210000382))",
            symbol="AS131",
            werkingsgebied_title="Maatwerkgebied glastuinbouw",
            werkingsgebied_uuid=uuid.UUID("00000000-0009-0000-0000-000000000001"),
            created_date=datetime(2023, 2, 2, 2, 2, 2),
            modified_date=datetime(2023, 2, 2, 2, 2, 2),
            start_validity=datetime(2023, 2, 2, 2, 2, 2),
            end_validity=None,
        )
        self._db.commit()

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
                UUID=uuid.UUID("00000000-0000-0003-0000-000000000001"),
                Title="Titel van het eerste beleidskeuze",
                Description="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eleifend lobortis libero, sit amet vestibulum lorem molestie sed. Cras felis mi, finibus eget dignissim id, pretium egestas elit. Cras sodales eleifend velit vel aliquet. Nulla dapibus sem at velit suscipit, at varius augue porttitor. Morbi tempor vel est id dictum. Donec ante eros, rutrum eu quam non, interdum tristique turpis. Donec odio ipsum, tincidunt ut dignissim vel, scelerisque ut ex. Sed sit amet molestie tellus. Vestibulum porta condimentum molestie. Praesent non facilisis nisi, in egestas mi.<p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Gebied_UUID=uuid.UUID("00000000-0009-0000-0000-000000000001"),
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
                UUID=uuid.UUID("00000000-0000-0003-0000-000000000002"),
                Title="Titel van het tweede beleidskeuze",
                Description="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eleifend lobortis libero, sit amet vestibulum lorem molestie sed. Cras felis mi, finibus eget dignissim id, pretium egestas elit. Cras sodales eleifend velit vel aliquet. Nulla dapibus sem at velit suscipit, at varius augue porttitor. Morbi tempor vel est id dictum. Donec ante eros, rutrum eu quam non, interdum tristique turpis. Donec odio ipsum, tincidunt ut dignissim vel, scelerisque ut ex. Sed sit amet molestie tellus. Vestibulum porta condimentum molestie. Praesent non facilisis nisi, in egestas mi. \n\nCurabitur porta dolor libero, auctor laoreet magna imperdiet tempus. Mauris at metus sit amet urna malesuada bibendum. Nulla ut tortor ut justo venenatis luctus nec vitae purus. Aliquam eget arcu sed ligula feugiat auctor. Integer at commodo turpis, id cursus enim. Pellentesque mattis posuere libero ut volutpat. Sed sagittis magna ac neque aliquam, eget scelerisque erat efficitur. Vivamus at erat rhoncus metus venenatis laoreet. Aliquam at pharetra leo. Vestibulum metus purus, molestie vel iaculis quis, suscipit nec velit. Nunc finibus felis quis iaculis posuere.</p>",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Gebied_UUID=uuid.UUID("00000000-0009-0000-0000-000000000001"),
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
                UUID=uuid.UUID("00000000-0000-0004-0000-000000000001"),
                Title="Titel van de eerste maatregel",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Gebied_UUID=uuid.UUID("00000000-0009-0000-0000-000000000001"),
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
                UUID=uuid.UUID("00000000-0000-0004-0000-000000000002"),
                Title="Titel van de tweede maatregel",
                Created_Date=datetime(2023, 2, 2, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 2, 3, 3, 3),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Modified_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Gebied_UUID=uuid.UUID("00000000-0009-0000-0000-000000000001"),
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
