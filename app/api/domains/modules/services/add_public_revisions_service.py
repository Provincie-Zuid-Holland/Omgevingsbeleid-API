from collections import defaultdict
from typing import Dict, List

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.domains.modules.types import PublicModuleObjectRevision
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable


class AddPublicRevisionsConfig(BaseModel):
    to_field: str
    object_codes: List[str]
    allowed_status_list: List[str]


class AddPublicRevisionsService:
    def __init__(
        self,
        db: Session,
        config: AddPublicRevisionsConfig,
        rows: List[BaseModel],
    ):
        self._db: Session = db
        self._config: AddPublicRevisionsConfig = config
        self._rows: List[BaseModel] = rows

    def add_revisions(self) -> List[BaseModel]:
        public_revisions_map: Dict[str, List[PublicModuleObjectRevision]] = self._fetch()

        for row in self._rows:
            code: str = getattr(row, "Code")
            if code in public_revisions_map:
                setattr(row, self._config.to_field, public_revisions_map[code])

        return self._rows

    def _fetch(self) -> Dict[str, List[PublicModuleObjectRevision]]:
        # group public statuses per module
        latest_status_subq = (
            select(
                ModuleStatusHistoryTable,
                ModuleTable.Title,
                func.row_number()
                .over(partition_by=ModuleStatusHistoryTable.Module_ID, order_by=desc(ModuleStatusHistoryTable.ID))
                .label("_StatusRowNumber"),
            )
            .join(ModuleStatusHistoryTable.Module)
            .filter(ModuleTable.is_active)
            .filter(ModuleStatusHistoryTable.Status.in_(self._config.allowed_status_list))
            .subquery("latest_status_subq")
        )

        # rank latest mod objects for this status
        module_objects_filtered_subq = (
            select(
                ModuleObjectsTable.Module_ID,
                ModuleObjectsTable.UUID,
                ModuleObjectsTable.Code,
                ModuleObjectsTable.Modified_Date,
                latest_status_subq.c.Status,
                latest_status_subq.c.Title,
                ModuleObjectContextTable.Action,
                func.row_number()
                .over(
                    partition_by=(ModuleObjectsTable.Module_ID, ModuleObjectsTable.Code),
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_ObjectRowNumber"),
            )
            .join(latest_status_subq, ModuleObjectsTable.Module_ID == latest_status_subq.c.Module_ID)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(
                latest_status_subq.c._StatusRowNumber == 1,
                ModuleObjectsTable.Modified_Date <= latest_status_subq.c.Created_Date,
                ModuleObjectContextTable.Code.in_(self._config.object_codes),
                ModuleObjectContextTable.Hidden == False,
            )
            .subquery("module_objects_filtered_subq")
        )

        # assemble query and pick the latest object for each module
        stmt = (
            select(
                module_objects_filtered_subq.c.Module_ID.label("Module_ID"),
                module_objects_filtered_subq.c.Title.label("Module_Title"),
                module_objects_filtered_subq.c.Status.label("Module_Object_Status"),
                module_objects_filtered_subq.c.UUID.label("Module_Object_UUID"),
                module_objects_filtered_subq.c.Code.label("Module_Object_Code"),
                module_objects_filtered_subq.c.Action.label("Action"),
                ModuleTable.Current_Status.label("Module_Status"),
            )
            .select_from(module_objects_filtered_subq)
            .join(ModuleTable, module_objects_filtered_subq.c.Module_ID == ModuleTable.Module_ID)
            .filter(module_objects_filtered_subq.c._ObjectRowNumber == 1)
            .order_by(desc(module_objects_filtered_subq.c.Modified_Date))
        )

        public_revisions_map: Dict[str, List[PublicModuleObjectRevision]] = defaultdict(list)
        db_result = self._db.execute(stmt).all()
        for db_row in db_result:
            public_revision: PublicModuleObjectRevision = PublicModuleObjectRevision.model_validate(db_row)
            public_revisions_map[public_revision.Module_Object_Code].append(public_revision)

        return public_revisions_map


class AddPublicRevisionsServiceFactory:
    def __init__(self, db: Session):
        self._db: Session = db

    def create_service(
        self,
        config: AddPublicRevisionsConfig,
        rows: List[BaseModel],
    ) -> AddPublicRevisionsService:
        return AddPublicRevisionsService(
            db=self._db,
            config=config,
            rows=rows,
        )
