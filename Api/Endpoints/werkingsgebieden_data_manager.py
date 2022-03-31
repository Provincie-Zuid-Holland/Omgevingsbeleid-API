# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from Api.Endpoints.data_manager import DataManager


class WerkingsgebiedenDataManager(DataManager):

    def _set_up_all_valid_view(self):
        """
        Set up a custom view that shows all valid version for werkingsgebieden
        """
        query = f"""
                    CREATE OR ALTER VIEW {self.all_valid_view} AS
                    SELECT
                        w.ID,
                        w.UUID,
                        w.Begin_Geldigheid,
                        w.Eind_Geldigheid,
                        w.Created_Date,
                        w.Modified_Date,
                        w.Created_By,
                        w.Modified_By,
                        w.Werkingsgebied,
                        w.symbol
                    FROM
                        Werkingsgebieden w
                    WHERE
                        w.UUID IN (
                            SELECT
                                m.Gebied
                            FROM
                                All_Valid_maatregelen m
                            UNION
                            SELECT
                                bw.Werkingsgebied_UUID
                            FROM
                                All_Valid_beleidskeuzes b
                                INNER JOIN Beleidskeuze_Werkingsgebieden bw ON b.UUID = bw.Beleidskeuze_UUID
                        )
                        AND UUID != '00000000-0000-0000-0000-000000000000'
                    """
        self._run_query_commit(query)

    def _set_up_valid_view(self):
        """
        Set up a custom view that shows the latest valid version for werkingsgebieden
        """
        query = f"""
                    CREATE OR ALTER VIEW {self.valid_view} AS
                    SELECT
                        w.ID,
                        w.UUID,
                        w.Begin_Geldigheid,
                        w.Eind_Geldigheid,
                        w.Created_Date,
                        w.Modified_Date,
                        w.Created_By,
                        w.Modified_By,
                        w.Werkingsgebied,
                        w.symbol
                    FROM 
                        (
                            SELECT *,
                            ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] 
                            FROM {self.schema.Meta.table}
                        ) w
                    WHERE
                        RowNumber = 1
                        AND w.UUID IN (
                            SELECT
                                m.Gebied
                            FROM
                                Valid_maatregelen m
                            UNION
                            SELECT
                                bw.Werkingsgebied_UUID
                            FROM
                                Valid_beleidskeuzes b
                                INNER JOIN Beleidskeuze_Werkingsgebieden bw ON b.UUID = bw.Beleidskeuze_UUID
                        )
                        AND UUID != '00000000-0000-0000-0000-000000000000'
                        AND Eind_Geldigheid > GETDATE()
                        AND Begin_Geldigheid <= GETDATE()
                    """
        self._run_query_commit(query)
