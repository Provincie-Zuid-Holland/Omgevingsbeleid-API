# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

# This endpoints shows the 10 latest edits on the specified objects

import re
from flask_restful import Resource
from datetime import datetime

class editView(Resource):
    def __init__(self, schemas):
        super().__init__()
        self.schemas=schemas
    
    def get(self):
        results = []
        for schema in self.schemas:
            manager = schema.Meta.manager(schema)
            rows = manager.get_latest_edits()
            for row in rows:
                row['Type'] = schema.Meta.slug
            results += rows
        
        # Dirty datetime fix until real fix is merged
        results = sorted(results, key=lambda r: datetime.fromisoformat(r['Modified_Date'][:-1]), reverse=True)


        return results, 200