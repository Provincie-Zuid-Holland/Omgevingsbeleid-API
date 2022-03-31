# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
"""
Collection of reference objects that contain logic for retrieving linkedobjects in the Database
"""

import marshmallow as MM


class UUID_Linker_Schema(MM.Schema):
    """
    Schema that represents a UUID_List_Reference
    """

    UUID = MM.fields.UUID(required=True, obprops=[])
    Koppeling_Omschrijving = MM.fields.Str(
        required=False, allow_none=True, missing="", default="", obprops=[]
    )


class UUID_List_Reference:
    def __init__(
        self,
        link_tablename,
        their_tablename,
        my_col,
        their_col,
        description_col,
        schema,
    ):
        self.link_tablename = link_tablename
        self.their_tablename = their_tablename
        self.my_col = my_col
        self.their_col = their_col
        self.description_col = description_col
        self.schema = schema()


class Reverse_UUID_Reference:
    def __init__(
        self,
        link_tablename,
        their_tablename,
        my_col,
        their_col,
        description_col,
        schema,
    ):
        self.link_tablename = link_tablename
        self.their_tablename = their_tablename
        self.my_col = my_col
        self.their_col = their_col
        self.description_col = description_col
        self.schema = schema()


class UUID_Reference:
    def __init__(self, target_tablename, schema):
        """An object that holds logic for references based on UUID

        Args:
            target_tablename (string): The name of the table to retrieve the object from
            schema (marshmallow.Schema): The schema used to serialize the retrieved object
        """
        self.target_tablename = target_tablename
        self.schema = schema()
