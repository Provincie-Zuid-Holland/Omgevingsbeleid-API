from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.dynamic.db import ObjectStaticsTable
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import (
    ModuleObjectContextTable,
    ModuleStatusHistoryTable,
    ModuleTable,
)
from app.extensions.modules.models.models import AllModuleStatusCode
from app.extensions.relations.db.tables import RelationsTable

from app.extensions.users.db import GebruikersTable
from app.core.security import get_password_hash


class DatabaseFixtures:
    def __init__(self, db: Session):
        self._db = db

    def create_all(self):
        self.create_users()
        self.create_object_statics()
        self.create_modules()
        self.create_relations()
        self.create_acknowledged_relations()

    def create_users(self):
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Gebruikersnaam="Anton",
                Email="test@example.com",
                Rol="Superuser",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000002"),
                Gebruikersnaam="Bert",
                Email="b@example.com",
                Rol="Ambtelijk opdrachtgever",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000003"),
                Gebruikersnaam="Cees",
                Email="c@example.com",
                Rol="Behandelend Ambtenaar",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000004"),
                Gebruikersnaam="Daniel",
                Email="d@example.com",
                Rol="Beheerder",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000005"),
                Gebruikersnaam="Emma",
                Email="e@example.com",
                Rol="Portefeuillehouder",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000006"),
                Gebruikersnaam="Fred",
                Email="f@example.com",
                Rol="Test runner",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
            )
        )
        self._db.add(
            GebruikersTable(
                UUID=uuid.UUID("11111111-0000-0000-0000-000000000007"),
                Gebruikersnaam="Gerald",
                Email="g@example.com",
                Rol="Tester",
                Status="Actief",
                Wachtwoord=get_password_hash("password"),
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
                Object_Type="beleidsdoel",
                Object_ID=1,
                Code="beleidsdoel-1",
                Owner_1_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
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
                Status=AllModuleStatusCode.Niet_Actief,
                Created_Date=datetime(2023, 2, 2, 2, 2, 2),
                Created_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            )
        )
        module.status_history.append(
            ModuleStatusHistoryTable(
                Status=AllModuleStatusCode.Vigerend,
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
                Action="Toevoegen",
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
                Title="Titel van de eerste ambitie",
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
                Action="Toevoegen",
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
                Action="Toevoegen",
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
                Action="Toevoegen",
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
                Action="Toevoegen",
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
                UUID=uuid.UUID("00000000-0000-0003-0000-000000000001"),
                Title="Titel van het eerste beleidskeuze",
                Description_Choice="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eleifend lobortis libero, sit amet vestibulum lorem molestie sed. Cras felis mi, finibus eget dignissim id, pretium egestas elit. Cras sodales eleifend velit vel aliquet. Nulla dapibus sem at velit suscipit, at varius augue porttitor. Morbi tempor vel est id dictum. Donec ante eros, rutrum eu quam non, interdum tristique turpis. Donec odio ipsum, tincidunt ut dignissim vel, scelerisque ut ex. Sed sit amet molestie tellus. Vestibulum porta condimentum molestie. Praesent non facilisis nisi, in egestas mi. ",
                Description_Operation="Curabitur porta dolor libero, auctor laoreet magna imperdiet tempus. Mauris at metus sit amet urna malesuada bibendum. Nulla ut tortor ut justo venenatis luctus nec vitae purus. Aliquam eget arcu sed ligula feugiat auctor. Integer at commodo turpis, id cursus enim. Pellentesque mattis posuere libero ut volutpat. Sed sagittis magna ac neque aliquam, eget scelerisque erat efficitur. Vivamus at erat rhoncus metus venenatis laoreet. Aliquam at pharetra leo. Vestibulum metus purus, molestie vel iaculis quis, suscipit nec velit. Nunc finibus felis quis iaculis posuere. ",
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
                Action="Toevoegen",
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
                UUID=uuid.UUID("00000000-0000-0003-0000-000000000002"),
                Title="Titel van het tweede beleidskeuze",
                Description_Choice="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse eleifend lobortis libero, sit amet vestibulum lorem molestie sed. Cras felis mi, finibus eget dignissim id, pretium egestas elit. Cras sodales eleifend velit vel aliquet. Nulla dapibus sem at velit suscipit, at varius augue porttitor. Morbi tempor vel est id dictum. Donec ante eros, rutrum eu quam non, interdum tristique turpis. Donec odio ipsum, tincidunt ut dignissim vel, scelerisque ut ex. Sed sit amet molestie tellus. Vestibulum porta condimentum molestie. Praesent non facilisis nisi, in egestas mi. \n\nCurabitur porta dolor libero, auctor laoreet magna imperdiet tempus. Mauris at metus sit amet urna malesuada bibendum. Nulla ut tortor ut justo venenatis luctus nec vitae purus. Aliquam eget arcu sed ligula feugiat auctor. Integer at commodo turpis, id cursus enim. Pellentesque mattis posuere libero ut volutpat. Sed sagittis magna ac neque aliquam, eget scelerisque erat efficitur. Vivamus at erat rhoncus metus venenatis laoreet. Aliquam at pharetra leo. Vestibulum metus purus, molestie vel iaculis quis, suscipit nec velit. Nunc finibus felis quis iaculis posuere. ",
                Description_Operation="",
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
                Action="Toevoegen",
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
                Action="Toevoegen",
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
                ID=1,
                Object_Type="beleidskeuze",
                Acknowledged=True,
                Acknowledged_Date=datetime(2023, 2, 2, 3, 3, 3),
                Acknowledged_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Title="Relatie naar beleidskeuze 2",
                Explanation="",
            ),
            AcknowledgedRelationSide(
                ID=2,
                Object_Type="beleidskeuze",
                Acknowledged=True,
                Acknowledged_Date=datetime(2023, 2, 3, 3, 3, 3),
                Acknowledged_By_UUID=uuid.UUID("11111111-0000-0000-0000-000000000001"),
                Title="Relatie naar beleidskeuze 1",
                Explanation="",
            ),
        )
        self._db.add(ack_table)
        self._db.commit()
