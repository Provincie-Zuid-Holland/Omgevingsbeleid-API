# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
import pyodbc
from Endpoints.errors import handle_odbc_exception
from globals import (
    db_connection_settings,
    max_datetime,
    min_datetime,
    null_uuid,
    row_to_dict,
)
from Endpoints.references import UUID_List_Reference, merge_references


class DataManagerException(Exception):
    pass


class DataManager:
    def __init__(self, schema):
        self.schema = schema
        required_meta_settings = ["slug", "table"]
        for setting in required_meta_settings:
            if setting not in dir(self.schema.Meta):
                raise DataManagerException(
                    f'Schema for manager does not define a field "{setting}"'
                )
        self.latest_view = f"Latest_{self.schema.Meta.slug}"
        self.valid_view = f"Valid_{self.schema.Meta.slug}"
        self.all_valid_view = f"All_Valid_{self.schema.Meta.slug}"

    def _set_up_all_valid_view(self):
        """
        Set up a view that shows the latest valid version for each lineage
        """
        # Check if we need to query for status
        status_condition = ""
        if status_conf := self.schema.Meta.status_conf:
            status_condition = f"AND {status_conf[0]} = '{status_conf[1]}'"
        query = f"""
                    CREATE OR ALTER VIEW {self.all_valid_view} AS
                    SELECT *
                    FROM {self.schema.Meta.table}
                    WHERE UUID != '00000000-0000-0000-0000-000000000000'
                    {status_condition}
                    """
    
        with pyodbc.connect(db_connection_settings, autocommit=True) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()



    def _set_up_latest_view(self):
        """
        Set up a view that shows the latest version for each lineage
        """
        query = f"""
                    CREATE OR ALTER VIEW {self.latest_view} AS 
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}) T
                    WHERE RowNumber = 1 
                    AND UUID != '00000000-0000-0000-0000-000000000000'
                    """

        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()

    def _set_up_valid_view(self):
        """
        Set up a view that shows the latest valid version for each lineage
        """
        # Check if we need to query for status
        status_condition = ""
        if status_conf := self.schema.Meta.status_conf:
            status_condition = f"AND {status_conf[0]} = '{status_conf[1]}'"
        query = f"""
                    CREATE OR ALTER VIEW {self.valid_view} AS
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}
                        WHERE UUID != '00000000-0000-0000-0000-000000000000'
                        AND Eind_Geldigheid > GETDATE()
                        AND Begin_Geldigheid < GETDATE()
                        {status_condition}) T 
                    WHERE RowNumber = 1
                    """
    
        with pyodbc.connect(db_connection_settings, autocommit=True) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()

    def get_all(
        self, valid_only=False, any_filters=None, all_filters=None, short=False, offset=None, limit=None
    ):
        """
        Retrieve all the latest versions for each lineage
        """
        
        self._set_up_latest_view()
        self._set_up_valid_view()
        
        query_args = []

        # determine view
        target_view = self.valid_view if valid_only else self.latest_view

        # determine the fields to include in the query
        fieldset = ["*"]
        if short:
            fieldset = [field for field in self.schema().fields_with_props("short")]
            

        query = f"""
                SELECT {', '.join(fieldset)} FROM {target_view} 
                """

        # generate filter_queries
        
        if any_filters or all_filters:
            query += "WHERE "
            if any_filters:
                query += "OR ".join(f"{key} = ? " for key in any_filters)
                query_args += [any_filters[key] for key in any_filters]
                if all_filters:
                    query += "AND "
            if all_filters:
                query += "AND ".join(f"{key} = ? " for key in all_filters)
                query_args += [all_filters[key] for key in all_filters]

        # Add ordering
        query += "ORDER BY Modified_Date DESC"

        # Add offset
        if offset:
            query += " OFFSET ? ROWS"
            query_args.append(offset)
        
        # Add limit
        if limit:
            query += " FETCH NEXT ? ROWS ONLY"
            query_args.append(limit)


        # WIP: Merge with inlining (might need a better strategy, might even go on view), should not scale by N_of_objects
        # TODO: Check wether views exist (and are valid, maybe later)
        
        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()
            result_rows = list(map(row_to_dict, cur.execute(query, *query_args)))
            result_rows = self.schema().dump(result_rows, many=True)

            

        
        all_references = {**self.schema.Meta.base_references,
                  **self.schema.Meta.references}
        
        included_references = all_references if (fieldset == ['*']) else {ref:all_references[ref] for ref in all_references if ref in fieldset}
        
        for ref in included_references:
            references = self._retrieve_references(included_references[ref], [row['UUID'] for row in result_rows])
            print(references)
        return result_rows

    def _retrieve_references(self, ref, source_uuids):
        if isinstance(ref, UUID_List_Reference):
            # Get the fieldset excluding references
            included_fields = [field for field in ref.schema.fields_without_props('referencelist')]
            
            query = f'''
                SELECT {included_fields}, {ref.description_col} FROM {ref.link_tablename}
                LEFT JOIN {ref.their_tablename} ON {ref.their_tablename}.UUID = {ref.their_col}
                WHERE {ref.my_col} in ?
                '''
            print(query)
            with pyodbc.connect(db_connection_settings, autocommit=False) as con:
                cur = con.cursor()
                result_rows = list(map(row_to_dict, cur.execute(query, source_uuids)))
            
            result_rows = ref.schema().dump(result_rows, many=True)
            return {row.pop(ref.my_col) : row for row in result_rows}

                

        

    def get_lineage(self, id, valid_only=False, any_filters=None, all_filters=None, short=False, offset=None, limit=None):
        """
        Retrieve all version of a single lineage
        """
        self._set_up_all_valid_view()

        # determine view/table to query
        target = self.all_valid_view if valid_only else self.schema().Meta.table
        
        fieldset = ['*']
        if short:
            fieldset = [field for field in self.schema().fields_with_props("short")]
        
        # ID is required
        query_args = [id]

        query = f"""
                SELECT {', '.join(fieldset)} FROM {target}
                WHERE ID = ? 
                """

        # generate filter_queries
        
        if any_filters or all_filters:
            query += "AND "
            if any_filters:
                query += "OR ".join(f"{key} = ? " for key in any_filters)
                query_args += [any_filters[key] for key in any_filters]
                if all_filters:
                    query += "AND "
            if all_filters:
                query += "AND ".join(f"{key} = ? " for key in all_filters)
                query_args += [all_filters[key] for key in all_filters]        

        # Add ordering
        query += "ORDER BY Modified_Date DESC"

        # Add offset
        if offset:
            query += " OFFSET ? ROWS"
            query_args.append(offset)
        
        # Add limit
        if limit:
            query += " FETCH NEXT ? ROWS ONLY"
            query_args.append(limit)

        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()
            result_rows = list(map(row_to_dict, cur.execute(query, *query_args)))
            result_rows = self.schema().dump(result_rows, many=True)
        
        all_references = {**self.schema.Meta.base_references,
                  **self.schema.Meta.references}.items()
        
        included_references = all_references if (fieldset == ['*']) else [ref for ref in all_references if ref in fieldset] 
        
        for ref in included_references:
            self._retrieve_references(ref, [row['UUID'] for row in result_rows])

        return result_rows

    def save(self, data, id=None):
        """
        [summary]

        Args:
            data (dict): the data to save
            id (int, optional): The ID of the lineage to add to. Defaults to None.
        """
        pass
