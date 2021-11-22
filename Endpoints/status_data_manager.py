from Endpoints.data_manager import DataManager


class StatusDataManager(DataManager):
    def __init__(self, schema):
        super().__init__(schema)
        self.detail_view = f"Detail_{self.schema.Meta.slug}"

    def _setup(self):
        super()._setup()
        print('Status manager setup')
        self.set_up_detail_view()

    def set_up_detail_view(self):
        """Creates the detail view for objects with status"""
        query = f"""
                CREATE OR ALTER VIEW {self.detail_view} AS
                SELECT cu.*, la.UUID as Latest_Version, la.Status as Latest_Status, va.UUID as Effective_Version FROM {self.schema().Meta.table} cu
                    LEFT JOIN Latest_beleidskeuzes la ON la.ID = cu.ID
                    LEFT JOIN Valid_beleidskeuzes va ON va.ID = cu.ID 
                """
        self._run_query_commit(query)

    def get_single_on_UUID(self, uuid):
        """Retrieve a single version of an object of this type, including the information about the lineage

        Args:
            uuid (string): the uuid of the target object
        """

        included_fields = ", ".join(
            [field for field in self.schema().fields_without_props(["referencelist"])]
        )

        query = f"""
            SELECT {included_fields} FROM {self.detail_view} WHERE UUID = ?
            """

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
