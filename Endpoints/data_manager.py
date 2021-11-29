# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
from collections import defaultdict
from marshmallow import schema
import pyodbc
from globals import (
    db_connection_settings,
    row_to_dict,
    ftc_name,
    stoplist_name,
)
from Endpoints.references import (
    Reverse_UUID_Reference,
    UUID_List_Reference,
    UUID_Reference,
)
from Endpoints.stopwords import stopwords
from uuid import UUID


class DataManagerException(Exception):
    pass


# TODO (sorted by prio):
# - Set up seperate tests for API & Data Manager

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
        # These fields should be present
        required_meta_settings = ["slug", "table"]
        for setting in required_meta_settings:
            if setting not in dir(self.schema.Meta):
                raise DataManagerException(
                    f'Schema for manager does not define a field "{setting}"'
                )
        self.latest_view = f"Latest_{self.schema.Meta.slug}"
        self.all_latest_view = f"All_Latest_{self.schema.Meta.slug}"
        self.valid_view = f"Valid_{self.schema.Meta.slug}"
        self.all_valid_view = f"All_Valid_{self.schema.Meta.slug}"

        self.read_fields = [
            field
            for field in self.schema().fields_without_props(
                ["referencelist", "calculated"]
            )
        ]

    def _setup(self):
        """Creates all the necessary views and indices"""
        print("Default manager setup")
        self._set_up_latest_view()
        self._set_up_all_latest_view()
        self._set_up_valid_view()
        self._set_up_all_valid_view()
        self._set_up_search()

    def _run_query_commit(self, query, values=[]):
        with pyodbc.connect(db_connection_settings, autocommit=True) as con:
            try:
                cur = con.cursor()
                result = cur.execute(query, *values)
                return list(map(row_to_dict, result.fetchall()))
            except pyodbc.DatabaseError as e:
                if e.args[0] == "No results.  Previous SQL was not a query.":
                    return None
                else:
                    print(query)
                    raise e
            except pyodbc.ProgrammingError as e:
                print(query)
                raise e

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
        self._run_query_commit(query)

    def _set_up_latest_view(self):
        """
        Set up a view that shows the latest version for each lineage that is still valid
        """
        query = f"""
                    CREATE OR ALTER VIEW {self.latest_view} AS 
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}) T
                    WHERE RowNumber = 1 
                    AND Eind_Geldigheid > GETDATE()
                    AND UUID != '00000000-0000-0000-0000-000000000000'
                    """

        self._run_query_commit(query)

    def _set_up_all_latest_view(self):
        """
        Set up a view that shows the latest version for each lineage
        """
        query = f"""
                    CREATE OR ALTER VIEW {self.all_latest_view} AS 
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}) T
                    WHERE RowNumber = 1 
                    AND UUID != '00000000-0000-0000-0000-000000000000'
                    """

        self._run_query_commit(query)

    def _set_up_valid_view(self):
        """
        Set up a view that shows the latest valid version for each lineage
        """
        # Check if we need to query for status
        status_condition = ""
        if status_conf := self.schema.Meta.status_conf:
            # e.g. "AND Status = 'Vigerend'"
            status_condition = f"WHERE {status_conf[0]} = '{status_conf[1]}'"

        query = f"""
                    CREATE OR ALTER VIEW {self.valid_view} AS
                    SELECT * FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.schema.Meta.table}
                        {status_condition}) T 
                    WHERE RowNumber = 1
                    AND UUID != '00000000-0000-0000-0000-000000000000'
                    AND Eind_Geldigheid > GETDATE()
                    AND Begin_Geldigheid <= GETDATE()
                    """

        self._run_query_commit(query)

    def get_single_on_UUID(self, uuid):
        """Retrieve a single version of an object of this type

        Args:
            uuid (string): the uuid of the target object
        """

        included_fields = ", ".join(
            [
                field
                for field in self.schema().fields_without_props(
                    ["referencelist", "calculated"]
                )
            ]
        )

        query = (
            f"SELECT {included_fields} FROM {self.schema().Meta.table} WHERE UUID = ?"
        )

        result_rows = self.schema().dump(
            self._run_query_commit(query, [uuid]), many=True
        )

        if not result_rows:
            return None

        # Get references
        all_references = {
            **self.schema.Meta.base_references,
            **self.schema.Meta.references,
        }

        included_references = all_references

        for ref in included_references:
            result_rows = self._retrieve_references(
                ref, included_references[ref], result_rows
            )

        return result_rows[0]

    def get_single_on_ID(self, id):
        """Retrieve a single version of an object of this type

        Args:
            id (int): the id of the target object
        """

        included_fields = ", ".join(
            [
                field
                for field in self.schema().fields_without_props(
                    ["referencelist", "calculated"]
                )
            ]
        )

        query = f"SELECT {included_fields} FROM {self.all_latest_view} WHERE ID = ?"

        result_rows = self.schema().dump(self._run_query_commit(query, [id]), many=True)

        if not result_rows:
            return None

        # Get references
        all_references = {
            **self.schema.Meta.base_references,
            **self.schema.Meta.references,
        }

        included_references = all_references

        for ref in included_references:
            result_rows = self._retrieve_references(
                ref, included_references[ref], result_rows
            )

        return result_rows[0]

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
            select_fieldset = [
                field
                for field in self.schema().fields_with_props(["short"])
                if field
                not in self.schema().fields_with_props(["referencelist", "calculated"])
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

        result_rows = self.schema().dump(
            self._run_query_commit(query, query_args), many=True
        )

        # Get references
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

    def _store_references(self, obj_uuid, ref, ref_datalist):
        """
        Store the linked references

        Args:
            obj_uuid (string): the object uuid that this ref belongs to
            ref (reference): A reference object
            ref_datalist (list): The data to store

        """
        if isinstance(ref, UUID_List_Reference):
            for ref_data in ref_datalist:
                query = f"""
                INSERT INTO {ref.link_tablename} ({ref.my_col}, {ref.their_col}, {ref.description_col}) VALUES (?, ?, ?)"""
                self._run_query_commit(
                    query,
                    [
                        obj_uuid,
                        ref_data["UUID"],
                        ref_data.get("Koppeling_Omschrijving") or "",
                    ],
                )

    def _retrieve_references(self, fieldname, ref, source_rows):
        """
        Retrieve the linked references for this set of objects

        Args:
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
                field
                for field in ref.schema.fields_without_props(
                    ["referencelist", "calculated"]
                )
            ]
        except AttributeError:
            # This is for objects that are not inheriting from base_schema (probably an user object)
            included_fields = list(ref.schema.fields.keys())

        if isinstance(ref, UUID_List_Reference):

            # Prepare for join query
            included_fields = [f"b.{field}" for field in included_fields]

            # Also query for the reference row (my column) in order to add the results to the correct objects
            included_fields.append(ref.my_col)

            source_uuids = ", ".join([f"'{row['UUID']}'" for row in source_rows])
            # Query from the Valid view, so only valid objects get inlined.

            query = f"""
                 SELECT {", ".join(included_fields)}, {ref.description_col} FROM {ref.link_tablename} a
                 JOIN Valid_{ref.their_tablename} b ON b.UUID = {ref.their_col}
                 WHERE a.{ref.my_col} in ({source_uuids})
                 """

            result_rows = self._run_query_commit(query, [])

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

            # If this inherits from base_schema we can ask for valid objects
            # target_tn =  f'Valid_{ref.target_tablename}' if isinstance(ref.schema, Base_Schema) else ref.target_tablename
            target_tn = ref.target_tablename

            if not target_uuids:
                return source_rows

            query = f"""
                    SELECT {', '.join(included_fields)} from {target_tn} WHERE UUID IN ({target_uuids}) 
                    """

            result_rows = self._run_query_commit(query, [])

            result_rows = ref.schema.dump(result_rows, many=True)
            row_map = {row["UUID"]: row for row in result_rows}
            for row in source_rows:
                row[fieldname] = row_map.get(row[fieldname])
            return source_rows

        if isinstance(ref, Reverse_UUID_Reference):
            source_uuids = ", ".join([f"'{row['UUID']}'" for row in source_rows])

            included_fields.append(ref.my_col)

            query = f"""
                    SELECT {', '.join(included_fields)} from {ref.link_tablename} a
                    INNER JOIN Valid_{ref.their_tablename} b
                    ON b.UUID = a.{ref.their_col} 
                    WHERE {ref.my_col} IN ({source_uuids}) 
                    """
            result_rows = self._run_query_commit(query, [])

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
            fieldset = [field for field in self.schema().fields_with_props(["short"])]
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

        result_rows = self.schema().dump(
            self._run_query_commit(query, query_args), many=True
        )

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

    def save(self, data):
        """
        [summary]

        Args:
            data (dict): the data to save
            id (int, optional): The ID of the lineage to add to. Defaults to None.
        """
        all_references = {
            **self.schema.Meta.base_references,
            **self.schema.Meta.references,
        }
        reference_cache = {}

        for ref in all_references:
            # Remove all except UUID_References
            if ref in data and not isinstance(all_references[ref], UUID_Reference):
                reference_cache[ref] = data.pop(ref)

        assert (
            "UUID" not in data
        ), "UUID can not be in data, it should be generated by the database"

        column_names, values = tuple(zip(*data.items()))
        parameter_marks = ", ".join(["?"] * len(column_names))
        query = f"""INSERT INTO {self.schema.Meta.table} ({', '.join(column_names)}) OUTPUT inserted.UUID, inserted.ID VALUES ({parameter_marks})"""

        res = self._run_query_commit(query, values)

        output = res[0]

        for ref in reference_cache:
            self._store_references(
                output["UUID"], all_references[ref], reference_cache[ref]
            )

        return self.get_single_on_UUID(output["UUID"])

        # new_object = store_references(new_object, schema, cursor)

        # # Up to here we have stored the references, and the object itself
        # included_fields = ", ".join(
        #     [field for field in schema().fields_without_props("referencelist")]
        # )
        # retrieve_query = (
        #     f"""SELECT {included_fields} FROM {schema.Meta.table} WHERE UUID = ?"""
        # )
        # return get_objects(retrieve_query, [new_object["UUID"]], schema(), cursor)[0]

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
            search_title_fields = self.schema.fields_with_props(["search_title"])
            search_description_fields = self.schema.fields_with_props(
                ["search_description"]
            )

            search_fields = []

            if search_title_fields:
                assert (
                    len(search_title_fields) == 1
                ), f"More then one search_title field defined on object {self.schema.Meta.slug}"

                search_fields.append(f"{search_title_fields[0]} Language 1043")

            if search_description_fields:

                search_description_fields = map(
                    lambda f: f"{f} Language 1043", search_description_fields
                )
                search_fields += search_description_fields

            if search_fields:
                cur.execute(
                    f"""CREATE FULLTEXT INDEX ON {self.schema.Meta.table} (
                                    {', '.join(search_fields)}
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

        title_field = self.schema.fields_with_props(["search_title"])[0]
        description_fields = self.schema.fields_with_props(["search_description"])

        # if there is only one value the CONCAT_WS will fail so we just add an empty string
        if len(description_fields) == 1:
            description_fields.append("''")

        args = " OR ".join([f'"{word}"' for word in query.split(" ")])

        _title_fields = f"""({self.schema.fields_with_props(["search_title"])[0]})"""
        _description_fields = f"""({', '.join((self.schema.fields_with_props(["search_description"])))})"""

        search_query = f"""
                        SELECT
                            v.UUID as UUID, 
                            {title_field} as Titel,
                            CONCAT_WS(' ', {', '.join(description_fields)}) as Omschrijving,
                            CAST(FLOOR(f.WeightedRank) as int) as RANK,
                            '{self.schema.Meta.slug}' as Type
                            FROM {self.valid_view} v INNER JOIN 
                            ( 
                                SELECT [KEY], SUM(Rank) as WeightedRank FROM
                                (
                                SELECT Rank * 1 as Rank, [KEY] from CONTAINSTABLE({self.schema.Meta.table}, {_title_fields}, ?)
                                    UNION
                                SELECT Rank * 0.5 as Rank, [KEY] from CONTAINSTABLE({self.schema.Meta.table}, {_description_fields}, ?)
                                ) as x GROUP BY [KEY]) as f
                            ON f.[KEY] = v.UUID
                            ORDER BY f.WeightedRank DESC"""
        result_rows = self._run_query_commit(search_query, [args, args])
        return result_rows

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

            description_fields = self.schema.fields_with_props(["search_description"])
            title_field = self.schema.fields_with_props(["search_title"])[0]
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
                or_filter = " OR ".join(
                    [f"bw.{ref.their_col} = ?" for _ in query_uuids]
                )
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

            result_rows = self._run_query_commit(search_query, query_uuids)
            return result_rows
