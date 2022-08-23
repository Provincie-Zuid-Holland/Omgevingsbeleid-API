from uuid import uuid4
from app.crud import crud_beleidsdoel
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.db.session import SessionLocal
from app.models import Beleidsdoel, Beleidsdoel_Ambities
from app.schemas.beleidsdoel import BeleidsdoelCreate
from app.schemas.relationships import AmbitieCreateShortInline
from app.core.config import settings

db = SessionLocal()

create = BeleidsdoelCreate(
    Begin_Geldigheid=datetime.now(),
    Eind_Geldigheid=datetime.now(),
    Titel="Titel",
    Omschrijving="Omschrijving",
    Weblink="Weblink",
    Ambities=[
        AmbitieCreateShortInline(UUID="B786487C-3E65-4DD8-B360-D2C56BF83172", Koppeling_Omschrijving="Omschrijving"),
        # AmbitieCreateShortInline(UUID="1234", Koppeling_Omschrijving="Omschrijving"),
    ]
)

print("\n\n\n")
print(create)
print("\n\n\n")
print(create.as_create_model())
print("\n\n\n")
print(create.as_create_relations())
print("\n\n\n")

obj_in_data = jsonable_encoder(
    create.as_create_model(),
    custom_encoder={
        datetime: lambda dt: dt,
    },
)

request_time = datetime.now()

obj_in_data["Created_By_UUID"] = settings.NULL_UUID
obj_in_data["Modified_By_UUID"] = settings.NULL_UUID
obj_in_data["Created_Date"] = request_time
obj_in_data["Modified_Date"] = request_time

db_obj = Beleidsdoel(**obj_in_data)
db.add(db_obj)

relations_data = create.as_create_relations()
relations_data.add_relations(db_obj, db)

db.commit()
db.refresh(db_obj)  
