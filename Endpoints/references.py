# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
"""
Collection of reference objects that contain logic for retrieving linkedobjects in the Database
"""

from globals import (db_connection_settings, max_datetime, min_datetime,
                     null_uuid, row_to_dict)


def merge_references(obj, schema, cursor):
    """
    Merges al references for this object

    Args:
        obj (dict): The object to merge
        cursor (pyodbc.cursor): A cursor with a database connection
    Returns:
        None
    """
    references = {**schema.Meta.base_references, **schema.Meta.references}
    for ref in references:
        if ref in obj:
            obj[ref] = references[ref].retrieve(obj[ref], cursor)
    return obj


class UUID_Reference:
    def __init__(self, target_tablename, schema):
        """An object that holds logic for references based on UUID
        
        Args:
            target_tablename (string): The name of the table to retrieve the object from
            schema (marshmallow.Schema): The schema used to serialize the retrieved object
        """
        self.target_tablename = target_tablename
        self.schema = schema()

    def retrieve(self, UUID, cursor):
        """This function retrieves the linked object from the appropiate table

        Args:
            UUID (uuid): The UUID that was in this field
            cursor (pyodbc.cursor): A cursor with a database connection
        
        Return:
            dict: The refered object 
        """
        if not UUID:
            # This happend when the UUID is the nill UUID (it is shown as None in the endpoints)
            return UUID

        # Retrieve all the fields we want to query
        included_fields = ', '.join(
            [field for field in self.schema.fields])
        query = f'SELECT {included_fields} FROM {self.target_tablename} WHERE UUID = ?'

        # Load the objects to ensure validation
        query_result = list(cursor.execute(query, UUID))
        
        if len(query_result) > 1:
            result_object = self.schema.load(map(row_to_dict, query_result), many=True)                       
            return(self.schema.dump(result_object, many=True))
        else:
            result_object = self.schema.load(row_to_dict(query_result[0]))                       
            return(self.schema.dump(result_object))