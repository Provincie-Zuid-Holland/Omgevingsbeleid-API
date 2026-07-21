import uuid
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from sqlalchemy import ColumnElement, Select, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.modules import ModuleObjectRepository
from app.api.domains.objects.repositories import ObjectRepository
from app.api.domains.others.repositories import StorageFileRepository
from app.api.domains.publications.repository import PublicationStorageFileRepository
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import AssetsTable, StorageFileTable
from app.core.tables.publications import PublicationStorageFileTable


type ObjectTableType = ObjectsTable | ModuleObjectsTable
type StorageFileTableType = StorageFileTable | PublicationStorageFileTable
type StorageFileRepositoryType = StorageFileRepository | PublicationStorageFileRepository
type SubjectTableType = StorageFileTableType | AssetsTable
type Report = Dict[SubjectTableType, List[str]]
type FilterStrategy = Callable[[type[ObjectTableType]], ColumnElement[bool]]
type KeyStrategy = Callable[[ObjectTableType], Iterable[uuid.UUID]]


class ObjectLookups:
    def __init__(
        self,
        session: Session,
        object_repository: ObjectRepository,
        module_object_repository: ModuleObjectRepository,
    ):
        self._session: Session = session
        self._object_repository: ObjectRepository = object_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository

    def create_all(
        self,
        filter_strategy: FilterStrategy,
        key_strategy: KeyStrategy,
    ):
        self._objects_lookup: Dict[uuid.UUID, List[ObjectTableType]] = self._create_lookup(
            ObjectsTable, self._object_repository, filter_strategy, key_strategy
        )
        self._module_objects_lookup: Dict[uuid.UUID, List[ObjectTableType]] = self._create_lookup(
            ModuleObjectsTable, self._module_object_repository, filter_strategy, key_strategy
        )

    def _create_lookup(
        self,
        table_type: type[ObjectsTable | ModuleObjectsTable],
        repository: BaseRepository,
        filter_strategy: FilterStrategy,
        key_strategy: KeyStrategy,
    ) -> Dict[uuid.UUID, List[ObjectTableType]]:
        stmt: Select = select(table_type).filter(filter_strategy(table_type))
        objects_with_files: Sequence[ObjectTableType] = repository.fetch_all(self._session, stmt)
        lookup: Dict[uuid.UUID, List[ObjectTableType]] = {}
        for object_current in objects_with_files:
            for key in key_strategy(object_current):
                lookup.setdefault(key, []).append(object_current)
        return lookup

    def get_log(self, subject_uuid: uuid.UUID) -> Optional[str]:
        objects: List[ObjectTableType] = self._objects_lookup.get(subject_uuid, [])
        module_objects: List[ObjectTableType] = self._module_objects_lookup.get(subject_uuid, [])
        parts = [f"valid object {o.Code}" for o in objects] + [
            f"module object {mo.Code} from module {mo.Module_ID}" for mo in module_objects
        ]
        return (" used in " + ", ".join(parts)) if parts else None
