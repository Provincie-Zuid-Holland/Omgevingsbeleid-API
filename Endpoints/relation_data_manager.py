from Endpoints.data_manager import DataManager


class RelationDataManager(DataManager):
    def __init__(self, schema):
        if self.schema.Meta.slug != 'beleidsrelaties':
            raise AssertionError('This manager should only be used on beleidsrelaties')
        super().__init__(schema)
        self.ID_view = f"ID_{self.schema.Meta.slug}"
    
    def _setup(self):
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
    
    def _set_up_valid_view(self):
        query = f"""
              CREATE OR ALTER VIEW {self.valid_view} AS
                    SELECT T.ID, T.UUID,  vbk.UUID as Van_Beleidskeuze, nbk.UUID as Naar_Beleidskeuze, T.Omschrijving, T.Status, T.Aanvraag_Datum, T.Datum_Akkoord, T.Begin_Geldigheid, T.Eind_Geldigheid, T.Created_By, T.Created_Date, T.Modified_By, T.Modified_Date     FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.ID_view}) T 
					JOIN Valid_beleidskeuzes vbk ON vbk.ID = T.Van_Beleidskeuze
					JOIN Valid_beleidskeuzes nbk ON vbk.ID = T.Naar_Beleidskeuze
                    WHERE T.RowNumber = 1
                    AND T.UUID != '00000000-0000-0000-0000-000000000000'
                    AND T.Eind_Geldigheid > GETDATE()
                    AND T.Begin_Geldigheid <= GETDATE()
                """

    def _set_up_latest_view(self):
        query = f"""
              CREATE OR ALTER VIEW {self.latest_view} AS
                    SELECT T.ID, T.UUID,  vbk.UUID as Van_Beleidskeuze, nbk.UUID as Naar_Beleidskeuze, T.Omschrijving, T.Status, T.Aanvraag_Datum, T.Datum_Akkoord, T.Begin_Geldigheid, T.Eind_Geldigheid, T.Created_By, T.Created_Date, T.Modified_By, T.Modified_Date     FROM 
                        (SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                        FROM {self.ID_view}) T 
					JOIN Valid_beleidskeuzes vbk ON vbk.ID = T.Van_Beleidskeuze
					JOIN Valid_beleidskeuzes nbk ON vbk.ID = T.Naar_Beleidskeuze
                    WHERE T.RowNumber = 1
                    AND T.UUID != '00000000-0000-0000-0000-000000000000'
                    AND T.Eind_Geldigheid > GETDATE()
                    AND T.Begin_Geldigheid <= GETDATE()
                """
        