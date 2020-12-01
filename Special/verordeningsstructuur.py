import datetime
import marshmallow as MM
from flask import request, jsonify, abort
from flask_restful import Resource
import pyodbc
from flask_jwt_extended import get_jwt_identity
from globals import db_connection_settings
from xml.etree import ElementTree as ET
import re
import uuid
import time

class Tree_Root(MM.Schema):
    """
    Startpunt voor boomstructuur
    """
    Children = MM.fields.Nested("Tree_Node", many=True, allow_none=True)


class Tree_Node(MM.Schema):
    """
    Recursief schema voor boomstructuur
    """
    UUID = MM.fields.UUID(required=True)
    Children = MM.fields.Nested("self", many=True, allow_none=True)
    Titel = MM.fields.String(required=False, missing="", allow_none=True)
    Volgnummer = MM.fields.String(required=False, missing=None, allow_none=True)
    Type = MM.fields.String(required=True)
    Inhoud = MM.fields.String()

    class Meta:
        ordered = True
    
    @MM.post_dump()
    def uppercase(self, dumped, many):
        """
        Ensure UUID's are uppercase.
        """
        for field in dumped:
            try:
                uuid.UUID(dumped[field])
                dumped[field] = dumped[field].upper()
            except:
                pass
        return dumped


class Verordening_Structuur_Schema(MM.Schema):
    """
    Schema voor verordeningstructuur
    """
    ID = MM.fields.Integer(ob_auto=True)
    UUID = MM.fields.UUID(ob_auto=True)
    Titel = MM.fields.Str(required=True, ob_auto=False)
    Structuur = MM.fields.Nested(Tree_Root, ob_auto=False)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True, ob_auto=False)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True, ob_auto=False)
    Created_By = MM.fields.UUID(required=True, ob_auto=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True, ob_auto=True)
    Modified_By = MM.fields.UUID(required=True, ob_auto=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True, ob_auto=True)
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Vigerend', 'Concept', 'Vervallen'])], ob_auto=False)

    class Meta:
        ordered = True
    
    @MM.post_dump()
    def uppercase(self, dumped, many):
        """
        Ensure UUID's are uppercase.
        """
        for field in dumped:
            try:
                uuid.UUID(dumped[field])
                dumped[field] = dumped[field].upper()
            except:
                pass
        return dumped


def serialize_schema_to_xml(schema):
    """
    Turn a Verordening_Scructuur_Schema into a xml string
    """
    tree = ET.Element('tree', {'xmlns:xs': 'http://www.w3.org/2001/XMLSchema', 'xmlns': 'Verordening_Tree'})
    for child in schema['Children']:
        tree.append(_serialize_child_to_xml(child))
    return ET.tostring(tree, encoding='unicode', method='xml')


def _serialize_child_to_xml(childschema):
    childnode = ET.Element('child')
    uuid = ET.SubElement(childnode, 'uuid')
    uuid.text = str(childschema['UUID'])
    for child in childschema['Children']:
        childnode.append(_serialize_child_to_xml(child))
    return childnode


def remove_namespace(XMLtag):
    """
    Take a string generated from Elementtree .tag and clean it from the namespace identifier.
    Example:
        > remove_namespace('{MyNamespace}user') == 'user'
        > # True
    """
    return XMLtag.split('}')[-1]


def parse_schema_from_xml(_xml, vo_mappings):
    structure = ET.fromstring(_xml)
    if remove_namespace(structure.tag) != 'tree':
        return None
    result = {'Children': []}
    for child in structure:
        # if remove_namespace(child.tag) == 'uuid':
        #     result['UUID'] = child.text
        if remove_namespace(child.tag) == 'child':
            result['Children'].append(_parse_child_to_schema(child, vo_mappings))
    return result


def _parse_child_to_schema(xmlelement, vo_mappings):
    result = {'UUID': None, 'Titel': None, 'Children': []}
    for child in xmlelement:
        if remove_namespace(child.tag) == 'uuid':
            result['UUID'] = child.text.upper()
            result['Titel'] = vo_mappings[child.text.lower()][0]
            result['Volgnummer'] = vo_mappings[child.text.lower()][1]
            result['Type'] = vo_mappings[child.text.lower()][2]
            result['Inhoud'] = vo_mappings[child.text.lower()][3].replace('\r', '\n')
        if remove_namespace(child.tag) == 'child':
            result['Children'].append(_parse_child_to_schema(child, vo_mappings))
    return result


def row_to_dict(row):
    return dict(zip([t[0] for t in row.cursor_description], row))


def handle_odbc_exception(odbc_ex):
    pattern = re.compile(r'FK_\w+_(\w+)')
    match = pattern.search(odbc_ex.args[-1])
    if match:
        match = match.group(1)
        return {'message': f'Database integriteitsfout, een identifier naar een "{match}" object is niet geldig'}, 404
    code = odbc_ex.args[0]
    return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}, 500


def ob_auto_filter(field):
    return field.metadata.get('ob_auto', False)

def linked_objects(uuid):
    query = """SELECT b.UUID, b.Titel, b.Volgnummer, b.Type, b.Inhoud FROM 
        (SELECT UUID, T2.Loc.value('.','uniqueidentifier') as fk_Verordeningen
            FROM [dbo].[VerordeningStructuur] as T1	CROSS APPLY Structuur.nodes('declare namespace VT="Verordening_Tree";//VT:uuid') as T2(Loc)
            WHERE T2.Loc.value('.','uniqueidentifier') IN (SELECT UUID FROM Verordeningen) AND UUID = ?) AS a
    LEFT JOIN 
        (SELECT UUID, Titel, Volgnummer, Type, Inhoud FROM Verordeningen) AS b
    On a.fk_Verordeningen = b.UUID
    """
    results = {}
    with pyodbc.connect(db_connection_settings) as connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query, uuid)
        except pyodbc.Error as err:
            handle_odbc_exception(err)
        for row in cursor:
            results[row[0].lower()] = (row[1],row[2], row[3], row[4])
    return results
            
    

class Verordening_Structuur(Resource):

    def get(self, verordeningstructuur_id=None, verordeningstructuur_uuid=None):
        params = []
        filters = request.args.copy()
        limit = filters.pop("limit", None)
        if (filters and verordeningstructuur_uuid) or (filters and verordeningstructuur_id):
            return {'message': 'Filters en UUID/ID kunnen niet gecombineerd worden'}, 400
        if limit:
            query = f"SELECT TOP({limit}) * FROM Actuele_VerordeningStructuur"
        else:
            query = "SELECT * FROM Actuele_VerordeningStructuur"

        if verordeningstructuur_uuid:
            query += " WHERE UUID = ?"
            params.append(verordeningstructuur_uuid)

        elif verordeningstructuur_id:
            query += " WHERE ID = ? ORDER BY 'Modified_Date' ASC"
            params.append(verordeningstructuur_id)

        elif filters:
            
            invalids = [f for f in filters if f not in Verordening_Structuur_Schema().fields.keys()]
            if invalids:
                if invalids:
                    return {'message': f"Filter(s) '{' '.join(invalids)}' niet geldig voor dit type object."}, 403
            else:
                conditionals = [f"{f} = ?" for f in filters]
                conditional = " WHERE " + " AND ".join(conditionals)
                params = [filters[f] for f in filters]
                query = query + conditional
                
        rows = []

        with pyodbc.connect(db_connection_settings) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(query, *params)
                if cursor.rowcount == 0:
                    if verordeningstructuur_id:
                        return {'message': f'Object met ID={verordeningstructuur_id} niet gevonden'}, 404
                    if verordeningstructuur_uuid:
                        return {'message': f'Object met ID={verordeningstructuur_uuid} niet gevonden'}, 404
                for row in cursor:
                    rows.append(row)
            except pyodbc.Error as e:
                return handle_odbc_exception(e), 500

        results = []
        for row in rows:
            row = row_to_dict(row)
            row_linked_objects = linked_objects(row['UUID'])
            tree = Tree_Root().load(parse_schema_from_xml(row['Structuur'], row_linked_objects))
            row['Structuur'] = tree

            parsedrow = Verordening_Structuur_Schema().dump(row)
            results.append(parsedrow)
        if verordeningstructuur_uuid:
            return results[0]
        return results

    def post(self):
        if request.get_json() is None:
            return {'message': 'Request data empty'}, 400

        try:
            excluded = map(lambda k: k[0], filter(lambda k: ob_auto_filter(k[1]), Verordening_Structuur_Schema().fields.items()))
            read_schema = Verordening_Structuur_Schema(exclude=excluded, unknown=MM.RAISE)
            vo_object = read_schema.load(request.get_json())

        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        old_struct = vo_object['Structuur']

        if 'Structuur' in vo_object:
            vo_object['Structuur'] = serialize_schema_to_xml(vo_object['Structuur'])

        # Add missing data
        vo_object['Created_By'] = get_jwt_identity()['UUID']
        vo_object['Created_Date'] = datetime.datetime.now()
        vo_object['Modified_Date'] = vo_object['Created_Date']
        vo_object['Modified_By'] = vo_object['Created_By']

        keys, values = list(zip(*vo_object.items()))
        argmarks = ("? ," * len(keys))[:-2]

        create_query = f'''
        SET NOCOUNT ON
        DECLARE @generated_identifiers table ([uuid] uniqueidentifier, [id] int)

        INSERT INTO [VerordeningStructuur] ({', '.join(keys)}) OUTPUT inserted.UUID, inserted.ID into @generated_identifiers VALUES ({argmarks})

        SELECT uuid, id from @generated_identifiers
        '''

        with pyodbc.connect(db_connection_settings) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(create_query, *values)
                outputted = cursor.fetchone()
                uuid = outputted[0]
                id = outputted[1]
            except pyodbc.Error as e:
                return handle_odbc_exception(e), 500

        vo_object['Structuur'] = old_struct
        vo_object['UUID'] = uuid
        vo_object['ID'] = id

        return Verordening_Structuur_Schema().dump(vo_object), 200

    def patch(self, verordeningstructuur_id=None):
        if not verordeningstructuur_id:
            abort(404)

        if request.get_json() is None:
            return {'message': 'Request data empty'}, 400

        try:
            excluded = map(lambda k: k[0], filter(lambda k: ob_auto_filter(k[1]), Verordening_Structuur_Schema().fields.items()))
            read_schema = Verordening_Structuur_Schema(exclude=excluded, unknown=MM.RAISE, partial=True)
            vo_object = read_schema.load(request.get_json())

        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        old_struct = vo_object['Structuur']
        
        
        if 'Structuur' in vo_object:
            vo_object['Structuur'] = serialize_schema_to_xml(vo_object['Structuur'])

        query = f'''SELECT TOP(1) * FROM Verordeningstructuur WHERE ID = ? ORDER BY Modified_Date DESC'''
        with pyodbc.connect(db_connection_settings) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(query, verordeningstructuur_id)
                if cursor.rowcount == 0:
                    return {'message': f'Object met ID={verordeningstructuur_id} niet gevonden'}, 404
                old_vo_object = row_to_dict(cursor.fetchone())
            except pyodbc.Error as e:
                return handle_odbc_exception(e), 500

        new_vo_object = {**old_vo_object, **vo_object}

        # Add missing data
        new_vo_object['Modified_By'] = get_jwt_identity()['UUID']
        new_vo_object['Modified_Date'] = datetime.datetime.now()
        new_vo_object['ID'] = verordeningstructuur_id
        new_vo_object.pop('UUID')

        keys, values = list(zip(*new_vo_object.items()))
        argmarks = ("? ," * len(keys))[:-2]

        create_query = f'''
        SET NOCOUNT ON
        DECLARE @generated_identifiers table ([uuid] uniqueidentifier)

        INSERT INTO [VerordeningStructuur] ({', '.join(keys)}) OUTPUT inserted.UUID into @generated_identifiers VALUES ({argmarks})

        SELECT uuid from @generated_identifiers
        '''

        with pyodbc.connect(db_connection_settings) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(create_query, *values)
                outputted = cursor.fetchone()
                uuid = outputted[0]
                
            except pyodbc.Error as e:
                return handle_odbc_exception(e), 500

        new_vo_object['Structuur'] = old_struct
        new_vo_object['UUID'] = uuid

        return Verordening_Structuur_Schema().dump(new_vo_object), 200
