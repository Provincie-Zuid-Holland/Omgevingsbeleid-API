import records
from globals import db_connection_string
from uuid import UUID
from flask_restful.fields import Raw, MarshallingException
from queries import omgevingsbeleid_bij_beleidsbeslissing
import json
import marshmallow as MM 
from werkzeug.routing import BaseConverter

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

            
# Omgevingsbeleid (de)serialisatie

def flatten_obs(bb_uuid):
    """
    This is an utility function which collects al the linked Omgevingsbeleid
    objects linked to a Beleidsbelissings object and flattens them into a dictionary of lists
    """
    flattened = {}
    db = records.Database(db_connection_string)
    results = db.query(omgevingsbeleid_bij_beleidsbeslissing, uuid=bb_uuid)
    for row in results:
        for key in row.as_dict():
            
            if key.startswith('fk_') and not (row[key] is None):
                fieldname = key.replace('fk_', '')
                omschrijving_key = fieldname + '_Omschrijving'
                if fieldname in flattened:
                    flattened[fieldname].append({'UUID':row[key], 
                    'Omschrijving': row[omschrijving_key]})
                else:
                    flattened[fieldname]= [{'UUID':row[key], 
                    'Omschrijving': row[omschrijving_key]}]
    return flattened


def deflatten_obs(ob_dict):
    rows = []
    max_height = max(map(len, ob_dict.values()))
    for heigth in range(max_height):
        row = {}
        for key in ob_dict:
            if len(ob_dict[key]) > heigth:
                row[key] = ob_dict[key][heigth]
            else:
                row[key] = {'UUID': None, 'Omschrijving':None}
        rows.append(row)
    return rows     

# List URL serializer
class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split(',')
    def to_url(self, values):
        return ','.join(super(ListConverter, self).to_url(value) for value in values)