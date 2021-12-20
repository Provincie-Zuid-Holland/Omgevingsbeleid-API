from Endpoints.endpoint import FullList, parse_query_args, QueryArgError
from flask import request
from flask_jwt_extended import jwt_required
from Endpoints.errors import (
    handle_validation_filter_exception,
    handle_queryarg_exception,
)
import marshmallow as MM

class VersionedFullList(FullList):
    """
    A list of all the different lineages available in the database,
    showing the latests version of each object's lineage.
    """

    @jwt_required
    def get(self):
        """
        GET endpoint for a list of objects, shows the last object for each lineage
        """
        try:
            q_args = parse_query_args(
                request.args,
                self.schema().fields_without_props(["referencelist"]),
                self.schema(partial=True),
            )
        except QueryArgError as e:
            # Invalid filter keys
            return handle_queryarg_exception(e)
        except MM.exceptions.ValidationError as e:
            # Invalid filter values
            return handle_validation_filter_exception(e)

        manager = self.schema.Meta.manager(self.schema)
        
        all_rows = manager.get_all(
            False, q_args["any_filters"], q_args["all_filters"], True
        )
        valid_rows = manager.get_all(
            True, q_args["any_filters"], q_args["all_filters"], True
        )

        valids_map = {}
        for row in valid_rows:
            valids_map[row['ID']] = row
        
        
        for row in all_rows:
            
            row['Valid_version'] = valids_map.get(row['ID'])


        return all_rows, 200