import marshmallow as MM
from flask import request, jsonify
from flask_restful import Resource
import pyodbc
from flask_jwt_extended import get_jwt_identity
from globals import db_connection_settings, db_connection_string
from xml.etree import ElementTree as ET
import re


class Tree_Node(MM.Schema):
    """
    Recursief schema voor boomstructuur
    """
    UUID = MM.fields.UUID(required=True)
    Children = MM.fields.Nested("self", many=True, allow_none=True)

    class Meta:
        ordered = True


class Verordening_Structuur_Schema(MM.Schema):
    """
    Schema voor verordeningstructuur
    """
    ID = MM.fields.Integer(ob_auto=True)
    UUID = MM.fields.UUID(ob_auto=True)
    Structuur = MM.fields.Nested(Tree_Node, ob_auto=False)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True, ob_auto=False)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True, ob_auto=False)
    Created_By = MM.fields.UUID(required=True, ob_auto=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True, ob_auto=True)
    Modified_By = MM.fields.UUID(required=True, ob_auto=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True, ob_auto=True)
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Vigerend', 'Concept', 'Vervallen'])], ob_auto=False)

    class Meta:
        ordered = True


def serialize_schema_to_xml(schema):
    """
    Turn a Verordening_Scructuur_Schema into a xml string
    """
    tree = ET.Element('tree', {'xmlns:xs': 'http://www.w3.org/2001/XMLSchema', 'xmlns': 'Verordening_Tree'})
    # xml = ET.ElementTree(tree)
    uuid = ET.SubElement(tree, 'uuid')
    uuid.text = str(schema['UUID'])
    for child in schema['Children']:
        tree.append(_serialize_child_to_xml(child))
    return ET.tostring(tree, encoding='utf8', method='xml').decode()


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


def parse_schema_from_xml(_xml):
    structure = ET.fromstring(_xml)
    if remove_namespace(structure.tag) != 'tree':
        return None
    result = {'UUID': None, 'Children': []}
    for child in structure:
        if remove_namespace(child.tag) == 'uuid':
            result['UUID'] = child.text
        if remove_namespace(child.tag) == 'child':
            result['Children'].append(_parse_child_to_schema(child))
    return result


def _parse_child_to_schema(xmlelement):
    result = {'UUID': None, 'Children': []}
    for child in xmlelement:
        if remove_namespace(child.tag) == 'uuid':
            result['UUID'] = child.text
        if remove_namespace(child.tag) == 'child':
            result['Children'].append(_parse_child_to_schema(child))
    return result


def row_to_dict(row):
    return dict(zip([t[0] for t in row.cursor_description], row))


def handle_odbc_exception(odbc_ex):
    pattern = re.compile(r'FK_\w+_(\w+)')
    match = pattern.search(e.args[-1]).group(1)
    if match:
        return {'message': f'Database integriteitsfout, een identifier naar een "{match}" object is niet geldig'}, 404
    code = odbc_ex.args[0]
    return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}, 500

def ob_auto_filter(field):
    return field.metadata.get('ob_auto', False)

class Verordening_Structuur(Resource):

    def get(self, verordeningstructuur_id=None, verordeningstructuur_uuid=None):
        params = []
        filters = request.args
        if (filters and verordeningstructuur_uuid) or (filters and verordeningstructuur_id):
            return {'message': 'Filters en UUID/ID kunnen niet gecombineerd worden'}, 400
        query = "SELECT * FROM VerordeningStructuur"

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
                    if verordeningstructuur_id: return {'message': f'Object met ID={verordeningstructuur_id} niet gevonden'}, 404
                    if verordeningstructuur_uuid: return {'message': f'Object met ID={verordeningstructuur_uuid} niet gevonden'}, 404
                for row in cursor:
                    rows.append(row)
            except pyodbc.Error as e:
                return handle_odbc_exception(e), 500

        results = []
        for row in rows:
            row = row_to_dict(row)
            tree = Tree_Node().load(parse_schema_from_xml(row['Structuur']))
            row['Structuur'] = tree
            parsedrow = Verordening_Structuur_Schema().dump(row)
            results.append(parsedrow)
        if verordeningstructuur_uuid:
            return results[0]
        return results

    def post(self):
        try:
            excluded = map(lambda k: k[0], filter(lambda k: ob_auto_filter(k[1]), Verordening_Structuur_Schema().fields.items()))
            read_schema = Verordening_Structuur_Schema(exclude=excluded, unknown=MM.RAISE)
            parsed = read_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        if 'Structuur' in parsed:
            parsed['Structuur'] = serialize_schema_to_xml(parsed['Structuur'])
        return jsonify(parsed)