# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
from collections import defaultdict
import pyodbc
from globals import (
    db_connection_settings,
    row_to_dict,
    ftc_name,
    stoplist_name,
)
from Endpoints.references import (
    Reverse_ID_Reference,
    Reverse_UUID_Reference,
    UUID_List_Reference,
    ID_List_Reference,
    UUID_Reference,
    merge_references,
)
from Endpoints.stopwords import stopwords
from uuid import UUID


class DataManagerException(Exception):
    pass


# TODO (sorted by prio):
# - Graph view (only valids)
# - Single object (with auth)
# - Saving
# - Refector reference merging
# - Set up seperate tests for API & Data Manager

# Should validation be a part of this? We do have the schemas here.
# Catch errors in endpoint logic or here? What would determine that?
# Still waiting for UUID/ID meeting with team
# Effectivity -> becomes in effect (USA), Object that are in effect
# Generate query conditions in schemas (responsibility)
class DataManager:
    def __init__(self, schema):
        """A manager object for interacting with the database

        Args:
            schema (Marshmallow.Schema): The schema that defines this object

        Raises:
            DataManagerException: Settings are missing on schema
        """
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

    def _setup(self):
        """Creates all the necessary views and indices"""
        self._set_up_latest_view()
        self._set_up_valid_view()
        self._set_up_all_valid_view()
        self._set_up_search()

    def _set_up_all_valid_view(self):
        """
        Set up a view that shows all valid version for each lineage
        """
        # Check if we need to query for status
        status_condition = ""
        if status_conf := self.schema.Meta.status_conf:
            # e.g. "AND Status = 'Vigerend'"
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
            # e.g. "AND Status = 'Vigerend'"
            status_condition = f"AND {status_conf[0]} = '{status_conf[1]}'"

        # TODO do we want >= or <= on geldigheid?
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
        self,
        valid_only=False,
        any_filters=None,
        all_filters=None,
        short=False,
        offset=None,
        limit=None,
    ):
        """
        Retrieve all the objects of this type

        Args:
            valid_only (bool, optional): Only retrieve the objects that are valid. Defaults to False
            any_filters (str, optional): Filters that should apply to the objects (combined with OR). Defaults to None
            all_filters (str, optional): Filters that should apply to the objects (combined with AND). Defaults to None
            short (bool, optional): Wether to return a short representation of the objects. Defaults to False
            offset (int, optional): Offset results with this amount. Defaults to None (equals no offset)
            limit (int, optional): Return a max amount of objects, counted from offset. Defaults to None (equals no limit)

        Returns:
            List: The resulting objects
        """

        query_args = []

        # determine view
        target_view = self.valid_view if valid_only else self.latest_view

        # determine the fields to include in the query
        fieldset = ["*"]
        if short:
            fieldset = [field for field in self.schema().fields_with_props("short")]
            # skip references field in short
            select_fieldset = [
                field[0]
                for field in self.schema().fields.items()
                if (
                    "referencelist" not in field[1].metadata["obprops"]
                    and field[0] in fieldset
                )
            ]

        else:
            select_fieldset = fieldset

        query = f"""
                SELECT {', '.join(select_fieldset)} FROM {target_view} 
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

        with pyodbc.connect(db_connection_settings, autocommit=False) as con:
            cur = con.cursor()
            result_rows = list(map(row_to_dict, cur.execute(query, *query_args)))
            result_rows = self.schema().dump(result_rows, many=True)

        all_references = {
            **self.schema.Meta.base_references,
            **self.schema.Meta.references,
        }

        included_references = (
            all_references
            if (fieldset == ["*"])
            else {ref: all_references[ref] for ref in all_references if ref in fieldset}
        )

        for ref in included_references:
            result_rows = self._retrieve_references(
                ref, included_references[ref], result_rows
            )

        return result_rows

    def _retrieve_references(self, fieldname, ref, source_rows):
        """
        Retrieve the linked references for this set of objects

        Args:
            fieldname (string): A fieldname on which to store the references
            ref (reference): A reference object
            source_rows (list): The objects to add the references on

        Returns:
            List: The resulting objects with references added
        """
        if not source_rows:
            return source_rows
        # Get the fieldset excluding references
        try:
            included_fields = [
                field for field in ref.schema.fields_without_props("referencelist")
            ]
        except AttributeError:
            # This is for objects that are not inheriting from base_schema (probably an user object)
            included_fields = ref.schema.fields

        if isinstance(ref, UUID_List_Reference) or isinstance(ref, ID_List_Reference):
            # Also query for the reference row (my column) in order to add the results to the correct objects
            included_fields.append(ref.my_col)

            source_uuids = ", ".join([f"'{row['UUID']}'" for row in source_rows])
            query = f"""
                 SELECT {", ".join(included_fields)}, {ref.description_col} FROM {ref.link_tablename}
                 LEFT JOIN {ref.their_tablename} ON {ref.their_tablename}.UUID = {ref.their_col}
                 WHERE {ref.my_col} in ({source_uuids})
                 """

            with pyodbc.connect(db_connection_settings, autocommit=False) as con:
                cur = con.cursor()
                result_rows = list(map(row_to_dict, cur.execute(query)))

            row_map = defaultdict(list)
            for row in result_rows:
                row_map[row.pop(ref.my_col)].append(
                    {
                        "Koppeling_Omschrijving": row.pop(ref.description_col),
                        "Object": ref.schema.dump(row),
                    }
                )

            for row in source_rows:
                try:
                    row[fieldname] = row_map[row["UUID"]]
                except KeyError:
                    # No refs
                    row[fieldname] = []
            return source_rows

        if isinstance(ref, UUID_Reference):
            # collect the uuids to query
            target_uuids = ", ".join(
                [f"'{row[fieldname]}'" for row in source_rows if row.get(fieldname)]
            )

            if not target_uuids:
                return source_rows

            query = f"""
                    SELECT {', '.join(included_fields)} from {ref.target_tablename} WHERE UUID IN ({target_uuids}) 
                    """

            with pyodbc.connect(db_connection_settings, autocommit=False) as con:
                cur = con.cursor()
                result_rows = list(map(row_to_dict, cur.execute(query)))

            result_rows = ref.schema.dump(result_rows, many=True)
            row_map = {row["UUID"]: row for row in result_rows}
            for row in source_rows:
                row[fieldname] = row_map.get(row[fieldname])
            return source_rows

        if isinstance(ref, Reverse_UUID_Reference) or isinstance(
            ref, Reverse_ID_Reference
        ):
            source_uuids = ", ".join([f"'{row['UUID']}'" for row in source_rows])

            included_fields.append(ref.my_col)

            query = f"""
                    SELECT {', '.join(included_fields)} from {ref.link_tablename} 
                    INNER JOIN ( SELECT * FROM (SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber]
                        FROM All_Valid_{ref.their_tablename}) T WHERE RowNumber = 1) a
                    ON a.UUID = {ref.their_col}
                    WHERE {ref.my_col} IN ({source_uuids}) 
                    """

            with pyodbc.connect(db_connection_settings, autocommit=False) as con:
                cur = con.cursor()
                result_rows = list(map(row_to_dict, cur.execute(query)))

            row_map = defaultdict(list)
            for row in result_rows:
                row_map[row.pop(ref.my_col)].append(ref.schema.dump(row))

            for row in source_rows:
                if (not fieldname in row) or (not row[fieldname]):
                    row[fieldname] = []
                if row["UUID"] in row_map:
                    row[fieldname] += row_map[row["UUID"]]

            return source_rows

        return source_rows

    def get_lineage(
        self,
        id,
        valid_only=False,
        any_filters=None,
        all_filters=None,
        short=False,
        offset=None,
        limit=None,
    ):
        """
        Retrieve all the objects of this type that belong to the same lineage

        Args:
            self (int): An ID of a lineage
            valid_only (bool, optional): Only retrieve the objects that are valid. Defaults to False
            any_filters (str, optional): Filters that should apply to the objects (combined with OR). Defaults to None
            all_filters (str, optional): Filters that should apply to the objects (combined with AND). Defaults to None
            short (bool, optional): Wether to return a short representation of the objects. Defaults to False
            offset (int, optional): Offset results with this amount. Defaults to None (equals no offset)
            limit (int, optional): Return a max amount of objects, counted from offset. Defaults to None (equals no limit)

        Returns:
            List: The resulting objects
        """
        # determine view/table to query
        target = self.all_valid_view if valid_only else self.schema().Meta.table

        # determine the fields to include in the query
        fieldset = ["*"]
        if short:
            fieldset = [field for field in self.schema().fields_with_props("short")]
            # skip references field in short
            select_fieldset = [
                field[0]
                for field in self.schema().fields.items()
                if (
                    "referencelist" not in field[1].metadata["obprops"]
                    and field[0] in fieldset
                )
            ]

        else:
            select_fieldset = fieldset

        # ID is required
        query_args = [id]

        query = f"""
                SELECT {', '.join(select_fieldset)} FROM {target}
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

        all_references = {
            **self.schema.Meta.base_references,
            **self.schema.Meta.references,
        }

        included_references = (
            all_references
            if (fieldset == ["*"])
            else {ref: all_references[ref] for ref in all_references if ref in fieldset}
        )

        for ref in included_references:
            result_rows = self._retrieve_references(
                ref, included_references[ref], result_rows
            )

        return result_rows

    def save(self, data, id=None):
        """
        [summary]

        Args:
            data (dict): the data to save
            id (int, optional): The ID of the lineage to add to. Defaults to None.
        """
        pass

    def _set_up_search(self):
        """Creates the necessary indices for Full-Text-Search in SQL server, also adding stopwords to the database"""
        if not self.schema.Meta.searchable:
            return

        with pyodbc.connect(db_connection_settings, autocommit=True) as con:
            cur = con.cursor()

            # Check if a stoplist exists
            stoplists_exists = cur.execute(
                f"SELECT name FROM sys.fulltext_stoplists WHERE name = '{stoplist_name}';"
            )

            # if not, set it up
            if not stoplists_exists.rowcount:
                # Create stoplist
                cur.execute(f"CREATE FULLTEXT STOPLIST {stoplist_name};")

            # Populate stoplist
            words_in_stoplist = [
                row[0]
                for row in cur.execute(
                    f"SELECT stopword FROM sys.fulltext_stopwords w LEFT JOIN sys.fulltext_stoplists l ON w.stoplist_id = l.stoplist_id WHERE name = '{stoplist_name}'"
                )
            ]
            for word in stopwords:
                if word not in words_in_stoplist:
                    cur.execute(
                        f"""ALTER FULLTEXT STOPLIST {stoplist_name} ADD '{word}' LANGUAGE 1043;"""
                    )

            # Check for a catalog
            catalog_exists = cur.execute(
                f"SELECT name FROM sys.fulltext_catalogs WHERE name = '{ftc_name}'"
            )
            if not catalog_exists.rowcount:
                cur.execute(f"CREATE FULLTEXT CATALOG {ftc_name}")

            # Check is this table already has a search index set up
            ft_index_exists = list(
                cur.execute(
                    f"SELECT * FROM sys.fulltext_indexes WHERE object_id = object_id('{self.schema.Meta.table}')"
                )
            )

            if ft_index_exists:
                cur.execute(f"DROP FULLTEXT INDEX ON {self.schema.Meta.table}")

            # Set up new search
            search_title_fields = self.schema.fields_with_props("search_title")
            if search_title_fields:
                field = search_title_fields[0]
                cur.execute(
                    f"""CREATE FULLTEXT INDEX ON {self.schema.Meta.table} (
                                    {field} Language 1043
                                )
                                KEY INDEX PK_{self.schema.Meta.table}
                                ON {ftc_name}
                                WITH CHANGE_TRACKING = AUTO, STOPLIST = {stoplist_name}
                    """
                )

    def search(self, query):
        """
        Search for a given query.

        Args:
            query (str): the search query

        Returns:
            List: The object matching the query
        """
        if not self.schema.Meta.searchable:
            return

        title_field = self.schema.fields_with_props("search_title")[0]
        description_fields = self.schema.fields_with_props("search_description")

        # if there is only one value the CONCAT_WS will fail so we just add an empty string
        if len(description_fields) == 1:
            description_fields.append("''")

        args = " OR ".join([f'"{word}"' for word in query.split(" ")])

        search_query = f"""
                        SELECT
                            v.UUID as UUID, 
                            {title_field} as Titel,
                            CONCAT_WS(' ', {', '.join(description_fields)}) as Omschrijving,
                            RANK,
                            '{self.schema.Meta.slug}' as Type
                            FROM
                CONTAINSTABLE({self.schema.Meta.table}, *, ?) ct
                INNER JOIN {self.valid_view} v ON ct.[KEY] = v.UUID
                ORDER BY RANK DESC"""

        with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
            cursor = connection.cursor()
            return list(map(row_to_dict, cursor.execute(search_query, args)))

    def geo_search(self, query):
        """
        Search for a given query and find all objects linked to this.

        Args:
            query (str): list of UUIDs to match

        Returns:
            List: The objects matching the query
        """
        if not self.schema.Meta.geo_searchable or (
            self.schema.Meta.geo_searchable not in self.schema.Meta.references
        ):
            return []
        else:
            ref_key, ref = (
                self.schema.Meta.geo_searchable,
                self.schema.Meta.references[self.schema.Meta.geo_searchable],
            )

            description_fields = self.schema.fields_with_props("search_description")
            title_field = self.schema.fields_with_props("search_title")[0]
            query_uuids = [UUID(uid) for uid in query.split(",")]

            # if there is only one value the CONCAT_WS will fail so we just add an empty string
            if len(description_fields) == 1:
                description_fields.append("''")

            if isinstance(ref, UUID_List_Reference):
                search_query = f"""
                    SELECT vbk.UUID,
                        vbk.{title_field} as Titel,
                        CONCAT_WS(' ', {', vbk.'.join(description_fields)}) as Omschrijving,    
                        '{self.schema.Meta.slug}' as Type,
                        bw.{ref.their_col} as Gebied,
                        100 AS RANK
                        FROM {self.valid_view} vbk
                    INNER JOIN {ref.link_tablename} bw ON vbk.UUID = bw.{ref.my_col}
                """
                # generate OR filters:
                or_filter = " OR ".join([f"bw.{ref.their_col} = ?" for _ in query_uuids])
                search_query += "WHERE " + or_filter

            if isinstance(ref, UUID_Reference):
                search_query = f"""
                    SELECT UUID, 
                    {title_field} as Titel,
                    CONCAT_WS(' ', {', '.join(description_fields)}) as Omschrijving,
                    '{self.schema.Meta.slug}' as Type,
                    {ref_key} as Gebied,
                    100 AS RANK
                    FROM {self.valid_view}
                """

                # generate OR filters:
                or_filter = " OR ".join([f"{ref_key} = ?" for _ in query_uuids])
                search_query += "WHERE " + or_filter

            with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
                cursor = connection.cursor()
                res = cursor.execute(search_query, query_uuids)
                return list(map(row_to_dict, res))
