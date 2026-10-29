import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.types.api_input_data import ActFrbr, BillFrbr
from app.core.tables.publications import PublicationBillTable, PublicationEnvironmentTable


class BillFrbrProvider:
    async def generate_frbr(
        self,
        session: AsyncSession,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
    ) -> BillFrbr:
        if environment.has_state:
            return await self._create_real(session, environment, act_frbr)

        return self._create_fake(environment, act_frbr)

    async def _create_real(
        self,
        session: AsyncSession,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
    ) -> BillFrbr:
        stmt = select(func.count()).select_from(PublicationBillTable)
        count: int = ((await session.execute(stmt)).scalar()) + 1
        id_suffix: str = f"{count}"
        result: BillFrbr = self._create(environment, act_frbr, id_suffix)
        return result

    def _create_fake(
        self,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
    ) -> BillFrbr:
        id_suffix: str = uuid.uuid4().hex[:8]
        result: BillFrbr = self._create(environment, act_frbr, id_suffix)
        return result

    def _create(
        self,
        environment: PublicationEnvironmentTable,
        act_frbr: ActFrbr,
        id_suffix: str,
    ) -> BillFrbr:
        work_other: str = f"{act_frbr.work_other}-{id_suffix}"

        timepoint: datetime = datetime.now(UTC)
        frbr: BillFrbr = BillFrbr(
            work_province_id=environment.province_id,
            work_country=environment.frbr_country,
            work_date=str(timepoint.year),
            work_other=work_other,
            expression_language=environment.frbr_language,
            expression_date=timepoint.strftime("%Y-%m-%d"),
            expression_version=1,
        )
        return frbr
