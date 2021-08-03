# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
from base_schema import Base_Schema
import pyodbc
from Endpoints.errors import handle_odbc_exception
from globals import (db_connection_settings, max_datetime, min_datetime,
                     null_uuid, row_to_dict)


class DataManagerException(Exception):
    pass


class DataManager:

    def __init__(self, schema):
        self.schema = schema
        required_fields = ['slug, table']
        for field in required_fields:
            if not self.schema_cls.Meta.get(field):
                raise DataManagerException(
                    f'Schema for manager does not define a field "{field}"')
        self.latest_view = f'Latest_{self.schema.Meta.slug}'
        self.valid_view = f'Valid_{self.schema.Meta.slug}'

    def _set_up_latest_view(self):
        """
        Set up a view that shows the latest version for each lineage
        """
        query = f'''
                    CREATE OR REPLACE VIEW {self.latest_view} AS 
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}) T
                    WHERE RowNumber = 1 
                    AND UUID != '00000000-0000-0000-0000-000000000000'
                    '''

        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()

            try:
                cur.execute(query)

            except pyodbc.DatabaseError as e:
                raise handle_odbc_exception(e)
            
            cur.commit()

    def _set_up_valid_view(self):
        """
        Set up a view that shows the latest valid version for each lineage
        """
        # Check if we need to query for status
        status_condition = ''
        if status_conf := self.schema.Meta.status_conf:
            status_condition = f'AND {status_conf[0]} = {status_conf[1]}'

        query = f'''
                    CREATE OR REPLACE VIEW {self.valid_view} AS
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}
                        WHERE UUID != '00000000-0000-0000-0000-000000000000'
                        AND Eind_Geldigheid > GETDATE()
                        AND Begin_Geligheid < GETDATE()
                        {status_condition}) T 
                    WHERE RowNumber = 1
                    '''

        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()
            try:
                cur.execute(query)

            except pyodbc.DatabaseError as e:
                raise handle_odbc_exception(e)
            
            cur.commit()

    def get_all(self, valid_only=False, any_filters=None, all_filters=None):
        """Retrieve all the latest versions for each lineage
        """
        filter_query = ''
        query_args = []
        
        
        # generate filter_queries
        if any_filters:
            filter_query += 'OR '.join(f'{key} = ? ' for key in any_filters)
            query_args += [any_filters[key] for key in any_filters]

        if any_filters and all_filters:
            # Combine the filter queries
            filter_query += 'AND '

        if all_filters:
            filter_query += 'AND '.join(f'{key} = ? ' for key in all_filters)
            query_args += [all_filters[key] for key in all_filters]

        # determine view
        target_view = self.valid_view if valid_only else self.latest_view

        query = f'''
                SELECT * FROM {target_view} 
                WHERE {any_filters} {all_filters}
                '''
        
        # TODO: Merge with inlining (might need a better strategy, might even go on view)
        # TODO: Offset implementation
        # TODO: Dynamic field sets (should not go in view)
        # TODO: Check wether views exist (and are valid, maybe later)

        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()
            try:
                cur.execute(query, **query_args)

            except pyodbc.DatabaseError as e:
                raise handle_odbc_exception(e)

            cur.commit()

    def get_lineage(self, id):
        """Retrieve all version of a single lineage
        """
        pass

    def save(self, data, id=None):
        """[summary]

        Args:
            data (dict): the data to save
            id (int, optional): The ID of the lineage to add to. Defaults to None.
        """
        pass
