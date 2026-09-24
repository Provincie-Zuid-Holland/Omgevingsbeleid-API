from collections import defaultdict

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.domains.modules.types import PublicModuleObjectRevision
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable


class AddPublicRevisionsConfig(BaseModel):
    to_field: str
    object_codes: list[str]
    allowed_status_list: list[str]


class AddPublicRevisionsService:
    def __init__(
        self,
        session: Session,
        config: AddPublicRevisionsConfig,
        rows: list[BaseModel],
    ):
        self._session: Session = session
        self._config: AddPublicRevisionsConfig = config
        self._rows: list[BaseModel] = rows

    def add_revisions(self) -> list[BaseModel]:
        public_revisions_map: dict[str, list[PublicModuleObjectRevision]] = self._fetch()

        for row in self._rows:
            code: str = row.code
            if code in public_revisions_map:
                setattr(row, self._config.to_field, public_revisions_map[code])

        return self._rows

    def _fetch(self) -> dict[str, list[PublicModuleObjectRevision]]:
        # group public statuses per module
        latest_status_subq = (
            select(
                ModuleStatusHistoryTable,
                ModuleTable.title,
                func.row_number()
                .over(partition_by=ModuleStatusHistoryTable.module_id, order_by=desc(ModuleStatusHistoryTable.id))
                .label("_status_row_number"),
            )
            .join(ModuleStatusHistoryTable.module)
            .filter(ModuleTable.is_active)
            .filter(ModuleStatusHistoryTable.status.in_(self._config.allowed_status_list))
            .subquery("latest_status_subq")
        )

        # rank latest mod objects for this status
        module_objects_filtered_subq = (
            select(
                ModuleObjectsTable.module_id,
                ModuleObjectsTable.id,
                ModuleObjectsTable.code,
                ModuleObjectsTable.modified_date,
                latest_status_subq.c.status,
                latest_status_subq.c.title,
                ModuleObjectContextTable.action,
                func.row_number()
                .over(
                    partition_by=(ModuleObjectsTable.module_id, ModuleObjectsTable.code),
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_object_row_number"),
            )
            .join(latest_status_subq, ModuleObjectsTable.module_id == latest_status_subq.c.module_id)
            .join(ModuleObjectsTable.module_object_context)
            .filter(
                latest_status_subq.c._status_row_number == 1,
                ModuleObjectsTable.modified_date <= latest_status_subq.c.created_date,
                ModuleObjectContextTable.code.in_(self._config.object_codes),
                ModuleObjectContextTable.hidden == False,
            )
            .subquery("module_objects_filtered_subq")
        )

        # assemble query and pick the latest object for each module
        stmt = (
            select(
                module_objects_filtered_subq.c.module_id.label("module_id"),
                module_objects_filtered_subq.c.title.label("module_title"),
                module_objects_filtered_subq.c.status.label("module_object_status"),
                module_objects_filtered_subq.c.id.label("module_object_id"),
                module_objects_filtered_subq.c.code.label("module_object_code"),
                module_objects_filtered_subq.c.action.label("action"),
                ModuleTable.current_status.label("module_status"),
            )
            .select_from(module_objects_filtered_subq)
            .join(ModuleTable, module_objects_filtered_subq.c.module_id == ModuleTable.module_id)
            .filter(module_objects_filtered_subq.c._object_row_number == 1)
            .order_by(desc(module_objects_filtered_subq.c.modified_date))
        )

        public_revisions_map: dict[str, list[PublicModuleObjectRevision]] = defaultdict(list)
        db_result = self._session.execute(stmt).all()
        for db_row in db_result:
            public_revision: PublicModuleObjectRevision = PublicModuleObjectRevision.model_validate(db_row)
            public_revisions_map[public_revision.module_object_code].append(public_revision)

        return public_revisions_map


class AddPublicRevisionsServiceFactory:
    def create_service(
        self,
        session: Session,
        config: AddPublicRevisionsConfig,
        rows: list[BaseModel],
    ) -> AddPublicRevisionsService:
        return AddPublicRevisionsService(
            session=session,
            config=config,
            rows=rows,
        )
