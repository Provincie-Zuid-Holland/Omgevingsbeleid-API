# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Api.Endpoints.data_manager import DataManager


class RelationDataManager(DataManager):
    def __init__(self, schema):
        if schema.Meta.slug != 'beleidsrelaties':
            # TODO: fix this
            raise AssertionError('This manager should only be used on beleidsrelaties')
        super().__init__(schema)
        self.ID_view = f"ID_{self.schema.Meta.slug}"
    
    def _setup(self):
        print("Relation manager setup")
        self.set_up_ID_view()
        super()._setup()
        
        
    def set_up_ID_view(self):
        """Create a view that shows the relation with ID's instead of UUID's"""
        query = f"""
            CREATE OR ALTER VIEW {self.ID_view} AS
                SELECT T.ID, T.UUID,  vbk.ID as Van_Beleidskeuze, nbk.ID as Naar_Beleidskeuze, T.Omschrijving, T.Status, T.Aanvraag_Datum, T.Datum_Akkoord, T.Begin_Geldigheid, T.Eind_Geldigheid, T.Created_By, T.Created_Date, T.Modified_By, T.Modified_Date    
            FROM Beleidsrelaties T
                JOIN Beleidskeuzes vbk ON vbk.UUID = T.Van_Beleidskeuze
                JOIN Beleidskeuzes nbk ON nbk.UUID = T.Naar_Beleidskeuze
        """
        self._run_query_commit(query)
    
    def _set_up_all_valid_view(self):
        """
        Set up a view that shows all valid version for each lineage
        """
        query = f"""
              CREATE OR ALTER VIEW {self.all_valid_view} AS
                    SELECT T.ID, T.UUID,
                     vbk.UUID as Van_Beleidskeuze,
                     nbk.UUID as Naar_Beleidskeuze,
                     T.Omschrijving,
                     T.Status,
                     T.Aanvraag_Datum,
                     T.Datum_Akkoord,
                     T.Begin_Geldigheid,
                     T.Eind_Geldigheid,
                     T.Created_By,
                     T.Created_Date,
                     T.Modified_By,
                     T.Modified_Date FROM 
                    {self.ID_view} T 
					JOIN Valid_beleidskeuzes vbk ON vbk.ID = T.Van_Beleidskeuze
					JOIN Valid_beleidskeuzes nbk ON nbk.ID = T.Naar_Beleidskeuze
                    AND T.UUID != '00000000-0000-0000-0000-000000000000'
                """
        self._run_query_commit(query)

    def _set_up_valid_view(self):
        query = f"""
              CREATE OR ALTER VIEW {self.valid_view} AS
                    SELECT T.ID, T.UUID,
                     vbk.UUID as Van_Beleidskeuze,
                     nbk.UUID as Naar_Beleidskeuze,
                     T.Omschrijving,
                     T.Status,
                     T.Aanvraag_Datum,
                     T.Datum_Akkoord,
                     T.Begin_Geldigheid,
                     T.Eind_Geldigheid,
                     T.Created_By,
                     T.Created_Date,
                     T.Modified_By,
                     T.Modified_Date FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.ID_view}) T 
					JOIN Valid_beleidskeuzes vbk ON vbk.ID = T.Van_Beleidskeuze
					JOIN Valid_beleidskeuzes nbk ON nbk.ID = T.Naar_Beleidskeuze
                    WHERE T.RowNumber = 1
                    AND T.UUID != '00000000-0000-0000-0000-000000000000'
                    AND T.Eind_Geldigheid > GETDATE()
                    AND T.Begin_Geldigheid <= GETDATE()
                """
        self._run_query_commit(query)

    def _set_up_latest_view(self):
        query = f"""
              CREATE OR ALTER VIEW {self.latest_view} AS
                    SELECT T.ID, T.UUID,  vbk.UUID as Van_Beleidskeuze, nbk.UUID as Naar_Beleidskeuze, T.Omschrijving, T.Status, T.Aanvraag_Datum, T.Datum_Akkoord, T.Begin_Geldigheid, T.Eind_Geldigheid, T.Created_By, T.Created_Date, T.Modified_By, T.Modified_Date     FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.ID_view}) T 
					JOIN Latest_beleidskeuzes vbk ON vbk.ID = T.Van_Beleidskeuze
					JOIN Latest_beleidskeuzes nbk ON nbk.ID = T.Naar_Beleidskeuze
                    WHERE T.RowNumber = 1
                    AND T.UUID != '00000000-0000-0000-0000-000000000000'
                    AND T.Eind_Geldigheid > GETDATE()
                    AND T.Begin_Geldigheid <= GETDATE()
                """
        self._run_query_commit(query)        
    
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
        target = self.all_valid_view
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
            self._run_query_fetch(query, query_args), many=True
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
            f"SELECT {included_fields} FROM {self.all_valid_view} WHERE UUID = ?"
        )

        result_rows = self.schema().dump(
            self._run_query_fetch(query, [uuid]), many=True
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