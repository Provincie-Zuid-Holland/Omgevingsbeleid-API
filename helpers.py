import records
from globals import db_connection_string
from uuid import UUID
from flask_restful.fields import Raw, MarshallingException

def dictkeys_tolower(dictionary):
    lower_dict = {}
    for key in dictionary.keys():
        lower_dict[key.lower()] = dictionary[key]
    return lower_dict

def single_object_by_uuid(objectname, query, **kwargs):
    uuid = kwargs.get('uuid')
    db = records.Database(db_connection_string)
    results = db.query(query,
                       uuid=uuid)
    return results.first()


def objects_from_query(tablename, query):
    db = records.Database(db_connection_string)
    results = db.query(query)
    return results

def related_objects_from_query(tablename, query, arguments):
    def resolve_related_objects(self, info, **kwargs):
        db = records.Database("sqlite:///mock.db")
        arguments_map = { k: self.get(v) for k,v in arguments.items()}
        results = db.query(query, **arguments_map)
        return results

    return resolve_related_objects

def validate_UUID(uuid_str):
    try:
        val = UUID(uuid_str, version=4)
        return val
    except ValueError:
        return False
        
# Custom Flask Restful fields
class UUIDfield(Raw):
    def format(self, value):
        try:
            val = UUID(value, version=4)
            return str(val)
        except ValueError as ve:
            raise MarshallingException(ve)
        