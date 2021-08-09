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
from Endpoints.references import merge_references


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
        print(status_condition)
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
        if any_filters or any_filters:
            query += "WHERE "
            query += "OR ".join(f"{key} = ? " for key in any_filters)
            query_args += [any_filters[key] for key in any_filters]
            query += "AND "
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
            try:
                result_rows = list(map(row_to_dict, cur.execute(query, *query_args)))
                result_rows = self.schema().dump(result_rows, many=True)

            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e)

        
        all_references = {**self.schema.Meta.base_references,
                  **self.schema.Meta.references}.items()
        
        included_references = [ref for ref in all_references if ref in fieldset]
        
        for ref in included_references:
            self._retrieve_references(ref)

        return result_rows

    def _retrieve_reference(self):
        pass

    def get_lineage(self, id):
        """
        Retrieve all version of a single lineage
        """
        pass

    def save(self, data, id=None):
        """
        [summary]

        Args:
            data (dict): the data to save
            id (int, optional): The ID of the lineage to add to. Defaults to None.
        """
        pass
