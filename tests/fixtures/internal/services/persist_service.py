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

import tests.fixtures.internal.spec.objects as objects_types
import tests.fixtures.internal.spec.modules as module_types
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
            # Base
            UserSpec: UserPersistHandler(),
            AssetSpec: AssetPersistHandler(),
            StorageFileSpec: StorageFilePersistHandler(),
            ObjectRelatedFileSpec: ObjectRelatedFilePersistHandler(),
            # Geo
            InputGeoWerkingsgebiedenSpec: InputGeoWerkingsgebiedenPersistHandler(),
            InputGeoOnderverdelingSpec: InputGeoOnderverdelingPersistHandler(),
            AreaSpec: AreaPersistHandler(),
            # Objects
            objects_types.BeleidsdoelSpec: objects_types.BeleidsdoelPersistHandler(),
            objects_types.BeleidskeuzeSpec: objects_types.BeleidskeuzePersistHandler(),
            objects_types.GebiedSpec: objects_types.GebiedPersistHandler(),
            objects_types.GebiedengroepSpec: objects_types.GebiedengroepPersistHandler(),
            objects_types.GebiedsaanwijzingSpec: objects_types.GebiedsaanwijzingPersistHandler(),
            objects_types.MaatregelSpec: objects_types.MaatregelPersistHandler(),
            # Module
            module_types.ModuleSpec: module_types.ModulePersistHandler(),
            module_types.ModuleStatusHistorySpec: module_types.ModuleStatusHistoryPersistHandler(),
            # Module Objects
            module_types.ModuleBeleidsdoelSpec: module_types.ModuleBeleidsdoelPersistHandler(),
            module_types.ModuleBeleidskeuzeSpec: module_types.ModuleBeleidskeuzePersistHandler(),
            module_types.ModuleGebiedSpec: module_types.ModuleGebiedPersistHandler(),
            module_types.ModuleGebiedengroepSpec: module_types.ModuleGebiedengroepPersistHandler(),
            module_types.ModuleGebiedsaanwijzingSpec: module_types.ModuleGebiedsaanwijzingPersistHandler(),
            module_types.ModuleMaatregelSpec: module_types.ModuleMaatregelPersistHandler(),
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
