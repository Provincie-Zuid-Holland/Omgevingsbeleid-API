from typing import Dict, List, Optional, Sequence, Type

from sqlalchemy.orm import Session

from app.core.db.base import Base
from tests.fixtures.internal.spec.area_spec import AreaPersistHandler, AreaSpec
from tests.fixtures.internal.spec.asset_spec import AssetPersistHandler, AssetSpec
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import (
    InputGeoOnderverdelingPersistHandler,
    InputGeoOnderverdelingSpec,
)
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import (
    InputGeoWerkingsgebiedenPersistHandler,
    InputGeoWerkingsgebiedenSpec,
)
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFilePersistHandler, ObjectRelatedFileSpec
from tests.fixtures.internal.spec.storage_file_spec import StorageFilePersistHandler, StorageFileSpec
from tests.fixtures.internal.spec.user_spec import UserSpec, UserPersistHandler
from tests.fixtures.internal.spec.modules import (
    ModuleSpec,
    ModulePersistHandler,
    ModuleStatusHistorySpec,
    ModuleStatusHistoryPersistHandler,
    ModuleBeleidsdoelSpec,
    ModuleBeleidsdoelPersistHandler,
    ModuleBeleidskeuzeSpec,
    ModuleBeleidskeuzePersistHandler,
    ModuleMaatregelSpec,
    ModuleMaatregelPersistHandler,
)
import tests.fixtures.internal.spec.objects as objects_types
from tests.fixtures.internal.types import (
    BasePersistHandler,
    PersistContext,
    Record,
    Spec,
    FixtureData,
    PersistRecord,
    Ref,
)


class PersistService[S: Spec, H: BasePersistHandler]:
    def __init__(self):
        self._handlers: Dict[Type[S], H] = {
            UserSpec: UserPersistHandler(),
            AssetSpec: AssetPersistHandler(),
            StorageFileSpec: StorageFilePersistHandler(),
            objects_types.BeleidsdoelSpec: objects_types.BeleidsdoelPersistHandler(),
            objects_types.BeleidskeuzeSpec: objects_types.BeleidskeuzePersistHandler(),
            objects_types.MaatregelSpec: objects_types.MaatregelPersistHandler(),
            InputGeoWerkingsgebiedenSpec: InputGeoWerkingsgebiedenPersistHandler(),
            InputGeoOnderverdelingSpec: InputGeoOnderverdelingPersistHandler(),
            AreaSpec: AreaPersistHandler(),
            ObjectRelatedFileSpec: ObjectRelatedFilePersistHandler(),
            ModuleSpec: ModulePersistHandler(),
            ModuleStatusHistorySpec: ModuleStatusHistoryPersistHandler(),
            ModuleBeleidsdoelSpec: ModuleBeleidsdoelPersistHandler(),
            ModuleBeleidskeuzeSpec: ModuleBeleidskeuzePersistHandler(),
            ModuleMaatregelSpec: ModuleMaatregelPersistHandler(),
        }

    def persist(self, records: List[Record[S]], session: Session) -> FixtureData:
        context: PersistContext = PersistContext()
        table_rows: List[Base] = []
        result_records: List[PersistRecord] = []

        for record in records:
            handler: Optional[H] = self._handlers.get(type(record.spec))
            if handler is None:
                raise RuntimeError(f"No persist handler for {type(record.spec)}")

            record_rows: Sequence[Base] = handler.to_rows(record, context)
            table_rows.extend(record_rows)

            fixture_ref: Optional[Ref] = (
                Ref(type(record.spec), record.spec.key) if record.spec.key is not None else None
            )
            result_records.append(
                PersistRecord(
                    spec=record.spec,
                    rows=list(record_rows),
                    primary_key=record.spec.get_table_primary_key(),
                    fixture_key=record.spec.key,
                    fixture_ref=fixture_ref,
                )
            )

        session.add_all(table_rows)
        session.flush()

        return FixtureData(
            records=result_records,
        )
