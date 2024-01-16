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
from app.extensions.werkingsgebieden.db.tables import WerkingsgebiedenTable


class DatabaseFixtures:
    def __init__(self, db: Session):
        self._db = db

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
        self._db.add(
            WerkingsgebiedenTable(
                UUID=uuid.UUID("00000000-0009-0000-0000-000000000001"),
                Title="Eerste gebied - V1",
                ID=1,
                Created_Date=datetime(2023, 2, 2, 2, 2, 2),
                Modified_Date=datetime(2023, 2, 2, 2, 2, 2),
                Start_Validity=datetime(2023, 2, 2, 2, 2, 2),
                End_Validity=datetime(2023, 3, 3, 3, 3, 3),
            )
        )
        self._db.add(
            WerkingsgebiedenTable(
                UUID=uuid.UUID("00000000-0009-0000-0000-000000000002"),
                Title="Eerste gebied - V2",
                ID=1,
                Created_Date=datetime(2023, 2, 3, 3, 3, 3),
                Modified_Date=datetime(2023, 2, 3, 3, 3, 3),
                Start_Validity=datetime(2023, 3, 3, 3, 3, 3),
                End_Validity=datetime(2030, 3, 3, 3, 3, 3),
            )
        )
        self._db.add(
            WerkingsgebiedenTable(
                UUID=uuid.UUID("00000000-0009-0000-0000-000000000003"),
                Title="Tweede gebied",
                ID=1,
                Created_Date=datetime(2023, 2, 4, 4, 4, 4),
                Modified_Date=datetime(2023, 2, 4, 4, 4, 4),
                Start_Validity=datetime(2023, 2, 4, 4, 4, 4),
                End_Validity=datetime(2030, 2, 4, 4, 4, 4),
            )
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
