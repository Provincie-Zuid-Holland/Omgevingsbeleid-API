from sqlalchemy.orm import Query, aliased, joinedload
from sqlalchemy.orm.util import AliasedClass

from app.crud.base import CRUDBase
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    def get(self, uuid: str) -> Ambitie:
        return (
            self.db.query(self.model)
            .options(joinedload(Ambitie.Beleidskeuzes))
            .filter(self.model.UUID == uuid)
            .one()
        )

    def search(self, query: str):
        sub_query: Query = self._build_valid_view_filter().subquery("inner")
        model_alias: AliasedClass = aliased(
            element=self.model, alias=sub_query, name="inner", adapt_on_names=True
        )

        final_query: Query = (
            self.db.query(model_alias)
        )

        return final_query.all()
        

ambitie = CRUDAmbitie(Ambitie)
