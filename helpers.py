import records
from graphql import GraphQLError

def single_object_by_id(objectname, query):
    def resolve_single_object(root, info, **kwargs):
        id = kwargs.get('id')
        db = records.Database("sqlite:///mock.db")
        results = db.query(query,
                           id=id)
        return results.first(
            default=GraphQLError(f'{objectname} met id {id} is niet gevonden'))
    return resolve_single_object

def objects_from_query(tablename, query):
    def resolve_objects(root, info, **kwargs):
        print(kwargs)
        db = records.Database("sqlite:///mock.db")
        results = db.query(query)
        return results
    return resolve_objects

def related_objects_from_query(tablename, query, arguments):
    def resolve_related_objects(self, info, **kwargs):
        db = records.Database("sqlite:///mock.db")
        arguments_map = { k: self.get(v) for k,v in arguments.items()}
        results = db.query(query, **arguments_map)
        return results

    return resolve_related_objects
