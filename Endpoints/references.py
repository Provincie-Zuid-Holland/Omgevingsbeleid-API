# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
"""
Collection of reference objects that contain logic for retrieving linkedobjects in the Database
"""

from functools import partial
from globals import (db_connection_settings, max_datetime, min_datetime,
                     null_uuid, row_to_dict)
import marshmallow as MM


class UUID_Linker_Schema(MM.Schema):
    """
    Schema that represents a UUID_List_Reference
    """
    UUID = MM.fields.UUID(required=True, obprops=[])
    Koppeling_Omschrijving = MM.fields.Str(
        required=False, missing='', default='', obprops=[])


def merge_references(obj, schema, cursor, inline=True):
    """
    Merges al references for this object

    Args:
        obj (dict): The object to merge
        schema (marshmallow.Schema): The schema of the object
        cursor (pyodbc.cursor): A cursor with a database connection
    Returns:
        None
    """
    references = {**schema.Meta.base_references,
                  **schema.Meta.references}.items()
    
    for name, ref in references:
        if 'only' in dir(schema) and schema.only and name not in schema.only:
            continue
        if isinstance(ref, UUID_List_Reference) or isinstance(ref, Reverse_UUID_Reference):
            if inline:
                obj[name] = ref.retrieve_inline(obj, cursor)
            else:
                obj[name] = ref.retrieve(obj, cursor)
        
        if isinstance(ref, UUID_Reference):

            if name in obj:
                if inline:
                    obj[name] = ref.retrieve_inline(obj[name], cursor)
                else:
                    obj[name] = ref.retrieve(obj[name], cursor)

        
    return obj


def store_references(obj, schema, cursor):
    """
    Stores al references for this object

    Args:
        obj (dict): The object to store the references of
        schema (marshmallow.Schema): The schema of the object
        cursor (pyodbc.cursor): A cursor with a database connection
    Returns:
        None
    """
    references = {**schema.Meta.base_references,
                  **schema.Meta.references}.items()

    for name, ref in references:
        if isinstance(ref, UUID_Reference):
            # This needs no further implementation (just stored in column)
            continue

        if isinstance(ref, UUID_List_Reference):
            if name in obj:
                ref.store(obj['UUID'], obj[name], cursor)
                obj[name] = ref.retrieve_inline(obj, cursor)

    return obj


class UUID_List_Reference:
    def __init__(self, link_tablename, their_tablename, my_col, their_col, description_col, schema):
        self.link_tablename = link_tablename
        self.their_tablename = their_tablename
        self.my_col = my_col
        self.their_col = their_col
        self.description_col = description_col
        self.schema = schema()

    def retrieve_inline(self, obj, cursor):
        """This function retrieves the linked object from the appropiate table and uses a schema to inline them

        Args:
            UUID (uuid): The UUID of this object
            cursor (pyodbc.cursor): A cursor with a database connection

        Return:
            dict: The refered object
        """
        # Retrieve all the fields we want to query
        try:
            included_fields = ', '.join(
                [field for field in self.schema.fields_without_props('referencelist')])
        # this happens when the inlined object is not based on a base_schema (most probably a user table)
        except AttributeError:
            included_fields = ', '.join(
                [field for field in self.schema.fields])

        query = f'''
        SELECT {included_fields}, {self.description_col} FROM {self.link_tablename}
        LEFT JOIN {self.their_tablename} ON {self.their_tablename}.UUID = {self.their_col}
        WHERE {self.my_col} = ?
        '''
        # Retrieve the objects
        query_result = list(cursor.execute(query, obj['UUID']))

        result_objects = []
        for res in query_result:
            res_row = row_to_dict(res)
            result_objects.append({
                'Koppeling_Omschrijving': res_row.pop(self.description_col),
                'Object': self.schema.dump(res_row)})

        return result_objects

    def retrieve(self, obj, cursor):
        """This function retrieves the linked object from the appropiate table and uses the default linker schema

        Args:
            UUID (uuid): The UUID of this object
            cursor (pyodbc.cursor): A cursor with a database connection

        Return:
            dict: The refered object
        """
        query = f'SELECT {self.their_col} as UUID, {self.description_col} as Koppeling_Omschrijving FROM {self.link_tablename} WHERE {self.my_col} = ?'
        # Retrieve the objects
        query_result = list(cursor.execute(query, obj['UUID']))
        result_objects = map(row_to_dict, query_result)
        return(UUID_Linker_Schema().dump(result_objects, many=True))

    def store(self, UUID, linked, cursor):
        """This function stores the linked object in the appropiate table

        Args:
            UUID (uuid): The UUID of this object
            cursor (pyodbc.cursor): A cursor with a database connection

        Return:
            dict: The refered object
        """

        for link in linked:
            link = UUID_Linker_Schema().load(link)
            query = f'''
                INSERT INTO {self.link_tablename} ({self.my_col}, {self.their_col}, {self.description_col}) VALUES (?, ?, ?)'''
            # Store the objects
            cursor.execute(query, UUID, link['UUID'], link.get(
                'Koppeling_Omschrijving'))


class ID_List_Reference(UUID_List_Reference):

    def retrieve(self, obj, cursor):
        """This function retrieves the linked object from the appropiate table and uses the default linker schema

        Args:
            UUID (uuid): The UUID of this object
            cursor (pyodbc.cursor): A cursor with a database connection

        Return:
            dict: The refered object
        """
        status_filter = ''
        # if self.schema.Meta.status_conf:
        #     field, value = self.schema.Meta.status_conf
        #     status_filter = f"""AND {field} = '{value}'"""

        query = f'''
            SELECT [b].[UUID] as UUID
                ,{self.description_col}	 	 
            FROM {self.link_tablename}
            
            LEFT JOIN {self.their_tablename} a ON a.UUID = {self.their_col}
            
            JOIN (SELECT * FROM
			    (SELECT *, Row_number() OVER (partition BY [ID]
			        ORDER BY [Modified_date] DESC) [RowNumber]
			        FROM {self.their_tablename}
			    WHERE UUID != '00000000-0000-0000-0000-000000000000' {status_filter}) T 
            WHERE rownumber = 1) b ON b.ID = a.ID
            WHERE {self.my_col} = ?'''

        # Retrieve the objects
        query_result = list(cursor.execute(query, obj['UUID']))
        result_objects = map(row_to_dict, query_result)

        return(UUID_Linker_Schema().dump(result_objects, many=True))

    def retrieve_inline(self, obj, cursor):
        try:
            included_fields = ', '.join(
                [f'b.{field}' for field in self.schema.fields_without_props('referencelist')])
        # this happens when the inlined object is not based on a base_schema (most probably a user table)
        except AttributeError:
            included_fields = ', '.join(
                [f'b.{field}' for field in self.schema.fields])

        status_filter = ''
        # if self.schema.Meta.status_conf:
        #     field, value = self.schema.Meta.status_conf
        #     status_filter = f"""AND {field} = '{value}'"""

        query = f'''
            SELECT {included_fields}
                ,{self.description_col}	 
            FROM {self.link_tablename}
            LEFT JOIN {self.their_tablename} a ON a.UUID = {self.their_col}            
            JOIN (SELECT * FROM
			    (SELECT *, Row_number() OVER (partition BY [ID]
			        ORDER BY [Modified_date] DESC) [RowNumber]
			        FROM {self.their_tablename}
			    WHERE UUID != '00000000-0000-0000-0000-000000000000' {status_filter}) T 
            WHERE rownumber = 1) b ON b.ID = a.ID
            WHERE {self.my_col} = ?'''

        # Retrieve the objects
        query_result = list(cursor.execute(query, obj['UUID']))

        result_objects = []

        for res in query_result:
            res_row = row_to_dict(res)
            result_objects.append({
                'Koppeling_Omschrijving': res_row.pop(self.description_col),
                'Object': self.schema.dump(res_row)})

        return result_objects


class Reverse_UUID_Reference:
    def __init__(self, link_tablename, their_tablename, my_col, their_col, description_col, schema):
        self.link_tablename = link_tablename
        self.their_tablename = their_tablename
        self.my_col = my_col
        self.their_col = their_col
        self.description_col = description_col
        self.schema = schema()

    def retrieve_inline(self, obj, cursor):
        """This function retrieves the linked object from the appropiate table and uses a schema to inline them

        Args:
            UUID (uuid): The UUID of this object
            cursor (pyodbc.cursor): A cursor with a database connection

        Return:
            dict: The refered object
        """
        # Retrieve all the fields we want to query
        try:
            included_fields = ', '.join(
                [field for field in self.schema.fields_without_props('referencelist')])
        # this happens when the inlined object is not based on a base_schema (most probably a user table)
        except AttributeError:
            included_fields = ', '.join(
                [field for field in self.schema.fields])

        query = f'''
        SELECT {included_fields} FROM {self.link_tablename}
        INNER JOIN ( SELECT {included_fields} FROM (SELECT {included_fields},
            ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber]
            FROM {self.their_tablename}) T WHERE RowNumber = 1) bk    
        ON bk.UUID = {self.their_col}
        WHERE {self.my_col} = ?
        '''

        # Retrieve the objects
        query_result = list(cursor.execute(query, obj['UUID']))
        result_objects = map(row_to_dict, query_result)
        return(self.schema.dump(result_objects, many=True))

    def retrieve(self, obj, cursor):
        """This function retrieves the linked object from the appropiate table and uses the default linker schema

        Args:
            UUID (uuid): The UUID of this object
            cursor (pyodbc.cursor): A cursor with a database connection

        Return:
            dict: The refered object
        """

        query = f'SELECT {self.their_col} as UUID, {self.description_col} as Koppeling_Omschrijving FROM {self.link_tablename} WHERE {self.my_col} = ?'
        # Retrieve the objects
        query_result = list(cursor.execute(query, obj['UUID']))
        result_objects = UUID_Linker_Schema().load(
            map(row_to_dict, query_result), many=True)
        return(UUID_Linker_Schema().dump(result_objects, many=True))


class Reverse_ID_Reference(Reverse_UUID_Reference):
    pass


class UUID_Reference:
    def __init__(self, target_tablename, schema):
        """An object that holds logic for references based on UUID

        Args:
            target_tablename (string): The name of the table to retrieve the object from
            schema (marshmallow.Schema): The schema used to serialize the retrieved object
        """
        self.target_tablename = target_tablename
        self.schema = schema()

    def retrieve_inline(self, UUID, cursor):
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
        try:
            included_fields = ', '.join(
                [field for field in self.schema.fields_without_props('referencelist')])
        # this happens when the inlined object is not based on a base_schema (most probably a user table)
        except AttributeError:
            included_fields = ', '.join(
                [field for field in self.schema.fields])

        query = f'SELECT {included_fields} FROM {self.target_tablename} WHERE UUID = ?'

        # Load the objects to ensure validation
        query_result = list(cursor.execute(query, UUID))

        try:
            assert(len(query_result) == 1)
        except AssertionError as e:
            # Needs to be resolved in a better way
            return None

        result_object = row_to_dict(query_result[0])
        return(self.schema.dump(result_object))

    def retrieve(self, UUID, cursor):
        return UUID
