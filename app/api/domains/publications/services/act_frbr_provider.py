from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.core.tables.publications import PublicationActTable, PublicationActVersionTable


class ActFrbrProvider:
    async def generate_frbr(self, session: AsyncSession, act: PublicationActTable) -> ActFrbr:
        expression_version: int = await self._get_next_expression_version(session, act.id)

        timepoint: datetime = datetime.now(UTC)
        frbr: ActFrbr = ActFrbr(
            Act_ID=act.id,
            Work_Province_ID=act.work_province_id,
            Work_Country=act.work_country,
            Work_Date=act.work_date,
            Work_Other=act.work_other,
            Expression_Language=act.environment.frbr_language,
            Expression_Date=timepoint.strftime("%Y-%m-%d"),
            Expression_Version=expression_version,
        )
        return frbr

    async def _get_next_expression_version(self, session: AsyncSession, act_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(PublicationActVersionTable)
            .filter(PublicationActVersionTable.act_id == act_id)
        )
        next_expression_version: int = (await session.execute(stmt)).scalar() + 1
        return next_expression_version
