from datetime import datetime, timezone
from sqlalchemy import select, or_
from sqlalchemy.orm import column_property, aliased, composite

from app.dynamic.db import ObjectsTable
from app.extensions.lineage_resolvers.models.models import NextObjectValidities

NEXT_VERSION_COMPOSITE_GROUP = "next_object_version"


def build_composite_next_version():
    inner_obj = aliased(ObjectsTable)

    # share filters to find next version of the object
    base_query = (
        select(inner_obj)
        .where(inner_obj.Code == ObjectsTable.Code)
        .where(inner_obj.Modified_Date > ObjectsTable.Modified_Date)
        .where(inner_obj.Start_Validity <= datetime.now(timezone.utc))
        .where(or_(inner_obj.End_Validity > datetime.now(timezone.utc),
                   inner_obj.End_Validity.is_(None)))
        .order_by(inner_obj.Modified_Date.asc())
        .limit(1)
        .correlate(ObjectsTable)
    )

    # add each next version computed field with the same composite group
    ObjectsTable.next_version_object_uuid = column_property(
        base_query.with_only_columns(inner_obj.UUID).scalar_subquery(),
        deferred=True,
        group=NEXT_VERSION_COMPOSITE_GROUP
    )

    ObjectsTable.next_version_start_validity = column_property(
        base_query.with_only_columns(inner_obj.Start_Validity).scalar_subquery(),
        deferred=True,
        group=NEXT_VERSION_COMPOSITE_GROUP
    )

    ObjectsTable.next_version_end_validity = column_property(
        base_query.with_only_columns(inner_obj.End_Validity).scalar_subquery(),
        deferred=True,
        group=NEXT_VERSION_COMPOSITE_GROUP
    )

    ObjectsTable.next_version_created_date = column_property(
        base_query.with_only_columns(inner_obj.Created_Date).scalar_subquery(),
        deferred=True,
        group=NEXT_VERSION_COMPOSITE_GROUP
    )

    ObjectsTable.next_version_modified_date = column_property(
        base_query.with_only_columns(inner_obj.Modified_Date).scalar_subquery(),
        deferred=True,
        group=NEXT_VERSION_COMPOSITE_GROUP
    )

    return composite(
        NextObjectValidities.create,
        ObjectsTable.next_version_object_uuid,
        ObjectsTable.next_version_start_validity,
        ObjectsTable.next_version_end_validity,
        ObjectsTable.next_version_created_date,
        ObjectsTable.next_version_modified_date,
        deferred=True,
        group=NEXT_VERSION_COMPOSITE_GROUP
    )
