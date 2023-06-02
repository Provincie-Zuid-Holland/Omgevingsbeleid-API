import base64
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import re
import sys
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_datetime
from typing import Optional
import uuid
import json
from pprint import pprint
import pytz
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import List, Optional, Set
import re
import base64
import sys
import io
from uuid import UUID, uuid4

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from pkg_resources import add_activation_listener
from sqlalchemy import desc
from app.dynamic.db.object_static_table import ObjectStaticsTable

from app.dynamic.db.objects_table import ObjectsTable
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.models.meta import ImageMeta
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable

from app.app import dynamic_app # noqa
from app.core.db.session import SessionLocal
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.users.repository.user_repository import UserRepository
from app.core.settings import settings


@dataclass
class ObjectWrapper:
    object_static: ObjectStaticsTable
    object: ObjectsTable
    module_object_context: ModuleObjectContextTable
    module_object: ModuleObjectsTable


timezone = pytz.UTC
timepoint = datetime.now(tz=timezone)
timepoint_minus_1 = timepoint - timedelta(seconds=1)
timepoint_plus_1 = timepoint + timedelta(seconds=1)
timepoint_plus_2 = timepoint + timedelta(seconds=2)

db = SessionLocal()
asset_repository = AssetRepository(db)

main_user_uuid = uuid.UUID("71B95453-7BE1-48DA-86BF-4DA0F739E1CD") # Tom v G)


module = ModuleTable(
    Module_ID=1,
    Activated=True,
    Closed=True,
    Successful=True,
    Temporary_Locked=True,
    Title="T0 - Previous production data is packed in this module.",
    Description="Previous production data is packed in this module.",
    Created_Date=timepoint_minus_1,
    Modified_Date=timepoint_minus_1,
    Created_By_UUID=main_user_uuid,
    Modified_By_UUID=main_user_uuid,
    Module_Manager_1_UUID=main_user_uuid,
)

module_histories = [
    ModuleStatusHistoryTable(
        Module_ID=1,
        Status=ModuleStatusCode.Niet_Actief,
        Created_Date=datetime(year=2000, month=1, day=1),
        Created_By_UUID=main_user_uuid,
    ),
    ModuleStatusHistoryTable(
        Module_ID=1,
        Status=ModuleStatusCode.Vastgesteld,
        Created_Date=timepoint_plus_1,
        Created_By_UUID=main_user_uuid,
    )
]


user_uuids = {u.UUID: u.UUID for u in UserRepository(db).get_all()}
# print()
# pprint(len(user_uuids))
# print()
# exit()


def _get_or_create_asset(img, created_date: datetime, created_by: UUID) -> AssetsTable:
    # Extract the image data and file extension
    image_data = img["src"].split(",")[1]
    ext = img["src"].split(";")[0].split("/")[1]

    # First check if the image already exists
    # if so; then we do not need to parse the image to gain the meta
    image_hash: str = sha256(image_data.encode("utf-8")).hexdigest()
    image_table: Optional[
        AssetsTable
    ] = asset_repository.get_by_hash_and_content(image_hash, image_data)
    if image_table is not None:
        return image_table

    picture_data = base64.b64decode(image_data)
    size = sys.getsizeof(picture_data)
    try:
        image = Image.open(io.BytesIO(picture_data))
    except UnidentifiedImageError:
        raise ValueError("Invalid image")
    width, height = image.size

    meta: ImageMeta = ImageMeta(
        ext=ext,
        width=width,
        height=height,
        size=size,
    )
    image_table = AssetsTable(
        UUID=uuid4(),
        Created_Date=created_date,
        Created_By_UUID=created_by,
        Lookup=image_hash[0:10],
        Hash=image_hash,
        Meta=json.dumps(meta.to_dict()),
        Content=image_data,
    )
    db.add(image_table)
    return image_table

def _handle_image(img, created_date: datetime, created_by: UUID):
    image_table: AssetsTable = _get_or_create_asset(img, created_date, created_by)
    img["src"] = f"[ASSET:{image_table.UUID}]"

def extract_images(content: str, created_date: datetime, created_by: UUID):
    soup = BeautifulSoup(content, "html.parser")
    for img in soup.find_all("img", src=re.compile("^data:image/")):
        _handle_image(img, created_date, created_by)

    return str(soup)


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def guard_invalid_user(user: Optional[uuid.UUID]) -> Optional[uuid.UUID]:
    if user is None:
        return None
    if user not in user_uuids:
        return main_user_uuid
    return user


def create_object_static(data: dict, mapping: dict) -> ObjectStaticsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    os = ObjectStaticsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,
        
        Owner_1_UUID=guard_invalid_user(uuid.UUID(data.get("Eigenaar_1")) if data.get("Eigenaar_1", "") else None),
        Owner_2_UUID=guard_invalid_user(uuid.UUID(data.get("Eigenaar_2")) if data.get("Eigenaar_2", "") else None),
        Portfolio_Holder_1_UUID=guard_invalid_user(uuid.UUID(data.get("Portefeuillehouder_1")) if data.get("Portefeuillehouder_1", "") else None),
        Portfolio_Holder_2_UUID=guard_invalid_user(uuid.UUID(data.get("Portefeuillehouder_2")) if data.get("Portefeuillehouder_2", "") else None),
        Client_1_UUID=guard_invalid_user(uuid.UUID(data.get("Opdrachtgever")) if data.get("Opdrachtgever", "") else None),

        Cached_Title=data.get("Titel"),
    )

    return os


def create_ambitie(data: dict, mapping: dict) -> ObjectsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    Start_Validity: Optional[datetime] = parse_datetime(data.get("Begin_Geldigheid"))
    if Start_Validity.year < 2000:
        Start_Validity = parse_datetime(data.get("Created_Date"))

    End_Validity: Optional[datetime] = parse_datetime(data.get("Eind_Geldigheid"))
    if End_Validity.year > 2300:
        End_Validity = None

    row = ObjectsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,

        UUID=uuid.UUID(data.get("UUID")),
        Title=data.get("Titel"),
        Description=data.get("Omschrijving"),
        IDMS_Link=data.get("Weblink"),

        Created_Date=parse_datetime(data.get("Created_Date")),
        Modified_Date=parse_datetime(data.get("Modified_Date")),

        Created_By_UUID=guard_invalid_user(uuid.UUID(data.get("Created_By"))),
        Modified_By_UUID=guard_invalid_user(uuid.UUID(data.get("Modified_By"))),

        Start_Validity=Start_Validity,
        End_Validity=End_Validity,
    )
    return row


def create_beleidsregel(data: dict, mapping: dict) -> ObjectsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    Start_Validity: Optional[datetime] = parse_datetime(data.get("Begin_Geldigheid"))
    if Start_Validity.year < 2000:
        Start_Validity = parse_datetime(data.get("Created_Date"))

    End_Validity: Optional[datetime] = parse_datetime(data.get("Eind_Geldigheid"))
    if End_Validity.year > 2300:
        End_Validity = None

    row = ObjectsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,

        UUID=uuid.UUID(data.get("UUID")),
        Title=data.get("Titel"),
        Description=data.get("Omschrijving"),
        Weblink=data.get("Externe_URL"),

        Created_Date=parse_datetime(data.get("Created_Date")),
        Modified_Date=parse_datetime(data.get("Modified_Date")),

        Created_By_UUID=guard_invalid_user(uuid.UUID(data.get("Created_By"))),
        Modified_By_UUID=guard_invalid_user(uuid.UUID(data.get("Modified_By"))),

        Start_Validity=Start_Validity,
        End_Validity=End_Validity,
    )
    return row


def create_belang(data: dict, mapping: dict) -> ObjectsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    Start_Validity: Optional[datetime] = parse_datetime(data.get("Begin_Geldigheid"))
    if Start_Validity.year < 2000:
        Start_Validity = parse_datetime(data.get("Created_Date"))

    End_Validity: Optional[datetime] = parse_datetime(data.get("Eind_Geldigheid"))
    if End_Validity.year > 2300:
        End_Validity = None

    row = ObjectsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,

        UUID=uuid.UUID(data.get("UUID")),
        Title=data.get("Titel"),
        Description=data.get("Omschrijving"),
        Weblink=data.get("Weblink"),

        Created_Date=parse_datetime(data.get("Created_Date")),
        Modified_Date=parse_datetime(data.get("Modified_Date")),

        Created_By_UUID=guard_invalid_user(uuid.UUID(data.get("Created_By"))),
        Modified_By_UUID=guard_invalid_user(uuid.UUID(data.get("Modified_By"))),

        Start_Validity=Start_Validity,
        End_Validity=End_Validity,
    )
    return row


def create_beleidsdoel(data: dict, mapping: dict) -> ObjectsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    Start_Validity: Optional[datetime] = parse_datetime(data.get("Begin_Geldigheid"))
    if Start_Validity.year < 2000:
        Start_Validity = parse_datetime(data.get("Created_Date"))

    End_Validity: Optional[datetime] = parse_datetime(data.get("Eind_Geldigheid"))
    if End_Validity.year > 2300:
        End_Validity = None

    row = ObjectsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,

        UUID=uuid.UUID(data.get("UUID")),
        Title=data.get("Titel"),
        Description=data.get("Omschrijving"),
        IDMS_Link=data.get("Weblink"),

        Created_Date=parse_datetime(data.get("Created_Date")),
        Modified_Date=parse_datetime(data.get("Modified_Date")),

        Created_By_UUID=guard_invalid_user(uuid.UUID(data.get("Created_By"))),
        Modified_By_UUID=guard_invalid_user(uuid.UUID(data.get("Modified_By"))),

        Start_Validity=Start_Validity,
        End_Validity=End_Validity,
    )
    return row


def create_beleidskeuze(data: dict, mapping: dict) -> ObjectsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    Start_Validity: Optional[datetime] = parse_datetime(data.get("Begin_Geldigheid"))
    if Start_Validity.year < 2000:
        Start_Validity = parse_datetime(data.get("Created_Date"))

    End_Validity: Optional[datetime] = parse_datetime(data.get("Eind_Geldigheid"))
    if End_Validity.year > 2300:
        End_Validity = None

    row = ObjectsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,

        UUID=uuid.UUID(data.get("UUID")),
        Title=data.get("Titel"),
        Description=data.get("Omschrijving_Keuze"),
        Cause=data.get("Aanleiding"),
        Provincial_Interest=data.get("Provinciaal_Belang"),
        Explanation=data.get("Omschrijving_Werking"),
        IDMS_Link=data.get("Weblink"),
        Decision_Number=data.get("Besluitnummer"),

        Gebied_UUID=keuze_gebied_map.get(uuid.UUID(data.get("UUID")), None),

        Created_Date=parse_datetime(data.get("Created_Date")),
        Modified_Date=parse_datetime(data.get("Modified_Date")),

        Created_By_UUID=guard_invalid_user(uuid.UUID(data.get("Created_By"))),
        Modified_By_UUID=guard_invalid_user(uuid.UUID(data.get("Modified_By"))),

        Start_Validity=Start_Validity,
        End_Validity=End_Validity,
    )
    return row


def create_maatregel(data: dict, mapping: dict) -> ObjectsTable:
    o_type = mapping.get("object_type")
    o_id = data.get("ID")
    o_code = f"{o_type}-{o_id}"

    Start_Validity: Optional[datetime] = parse_datetime(data.get("Begin_Geldigheid"))
    if Start_Validity.year < 2000:
        Start_Validity = parse_datetime(data.get("Created_Date"))

    End_Validity: Optional[datetime] = parse_datetime(data.get("Eind_Geldigheid"))
    if End_Validity.year > 2300:
        End_Validity = None

    created_date = parse_datetime(data.get("Created_Date"))
    created_by = guard_invalid_user(uuid.UUID(data.get("Created_By")))
    description = data.get("Toelichting") or ""
    description = extract_images(description, created_date, created_by)

    row = ObjectsTable(
        Object_Type=o_type,
        Object_ID=o_id,
        Code=o_code,

        UUID=uuid.UUID(data.get("UUID")),
        Title=data.get("Titel"),
        Description=description,

        IDMS_Link=data.get("Weblink"),
        Decision_Number=data.get("Besluitnummer"),

        Gebied_UUID=(uuid.UUID(data.get("Gebied")) if data.get("Gebied", "") else None),

        Created_Date=parse_datetime(data.get("Created_Date")),
        Modified_Date=parse_datetime(data.get("Modified_Date")),

        Created_By_UUID=guard_invalid_user(uuid.UUID(data.get("Created_By"))),
        Modified_By_UUID=guard_invalid_user(uuid.UUID(data.get("Modified_By"))),

        Start_Validity=Start_Validity,
        End_Validity=End_Validity,
    )
    return row


def create_module_context(row: ObjectsTable) -> ModuleObjectContextTable:
    c = ModuleObjectContextTable(
        Module_ID=1,
        Object_Type=row.Object_Type,
        Object_ID=row.Object_ID,
        Code=row.Code,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=row.Created_By_UUID,
        Modified_By_UUID=row.Modified_By_UUID,
        Original_Adjust_On=None,
        Action="Create",
        Explanation="",
        Conclusion="",
    )
    return c


def create_module_object(row: ObjectsTable) -> ModuleObjectsTable:
    module_object_uuid = uuid.uuid4()

    object_row_dict = deepcopy(row.__dict__)
    del object_row_dict["_sa_instance_state"]

    module_row = ModuleObjectsTable(**(object_row_dict))
    module_row.Module_ID = 1
    module_row.UUID = module_object_uuid
    module_row.Start_Validity = None
    module_row.End_Validity = None

    row.Adjust_On = module_object_uuid

    return module_row


mappings = {
    # "ambitie": {
    #     "object_type": "ambitie",
    #     "file": "Valid_ambities_202305301039.json",
    #     "json_data_key": "Valid_ambities",
    #     "object_constructor": create_ambitie,
    #     "module": True,
    # },
    # "nationaal_belang": {
    #     "object_type": "nationaal_belang",
    #     "file": "Valid_belangen_202305301039.json",
    #     "json_data_key": "Valid_belangen",
    #     "object_constructor": create_belang,
    #     "module": False,
    # },
    # "beleidsdoel": {
    #     "object_type": "beleidsdoel",
    #     "file": "Valid_beleidsdoelen_202305301039.json",
    #     "json_data_key": "Valid_beleidsdoelen",
    #     "object_constructor": create_beleidsdoel,
    #     "module": True,
    # },
    # "beleidskeuze": {
    #     "object_type": "beleidskeuze",
    #     "file": "Valid_beleidskeuzes_202305301039.json",
    #     "json_data_key": "Valid_beleidskeuzes",
    #     "object_constructor": create_beleidskeuze,
    #     "module": True,
    # },
    "beleidsregel": {
        "object_type": "beleidsregel",
        "file": "Valid_beleidsregels_202305301039.json",
        "json_data_key": "Valid_beleidsregels",
        "object_constructor": create_beleidsregel,
        "module": True,
    },
    # "maatregel": {
    #     "object_type": "maatregel",
    #     "file": "Valid_maatregelen_202305301039.json",
    #     "json_data_key": "Valid_maatregelen",
    #     "object_constructor": create_maatregel,
    #     "module": True,
    # },
}


keuze_gebied_content = read_json_file("./scripts/import/data/Beleidskeuze_Werkingsgebieden.json")
keuze_gebied_map = {}
for row in keuze_gebied_content["Beleidskeuze_Werkingsgebieden"]:
    keuze_gebied_map[uuid.UUID(row["Beleidskeuze_UUID"])] = uuid.UUID(row["Werkingsgebied_UUID"])


def unpack_data(data: dict, mapping: dict):
    data_key = list(data.keys())[0]

    for entry in data[data_key]:
        constructor_func = mapping["object_constructor"]

        object_static = create_object_static(entry, mapping)
        object_row = constructor_func(entry, mapping)

        if mapping["module"]:
            module_object_context = create_module_context(object_row)
            module_object_row = create_module_object(object_row)
        
        db.add(object_static)
        db.commit()
        db.add(object_row)
        db.commit()

        if mapping["module"]:
            db.add(module_object_context)
            db.commit()
            db.add(module_object_row)
            db.commit()

        object_static_row_dict = deepcopy(object_static.__dict__)
        del object_static_row_dict["_sa_instance_state"]
        object_row_dict = deepcopy(object_row.__dict__)
        del object_row_dict["_sa_instance_state"]
        pprint(object_static_row_dict)
        print()
        pprint(object_row_dict)
        print()

        if mapping["module"]:
            module_object_row_dict = deepcopy(module_object_row.__dict__)
            del module_object_row_dict["_sa_instance_state"]
            module_object_context_dict = deepcopy(module_object_context.__dict__)
            del module_object_context_dict["_sa_instance_state"]
            pprint(module_object_row_dict)
            print()
            pprint(module_object_context_dict)
        
        print("\n\n\n---------------\n\n\n")




# db.add(module)
# db.add(module_histories[0])
# db.add(module_histories[1])
# db.commit()

for mapping_key, mapping in mappings.items():
    file_path = f"./scripts/import/data/{mapping['file']}"
    data = read_json_file(file_path)
    unpack_data(data, mapping)


"""


DELETE FROM module_objects;
DELETE FROM module_object_context;
DELETE FROM module_status_history;
DELETE FROM modules;
DELETE FROM objects;
DELETE FROM object_statics;
DELETE FROM assets ;



"""