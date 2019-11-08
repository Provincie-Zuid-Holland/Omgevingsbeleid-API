import marshmallow as MM
from flask import request
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
    ID = MM.fields.Integer()
    UUID = MM.fields.UUID()
    Structuur = MM.fields.Nested(Tree_Node)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.UUID(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.UUID(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Vigerend', 'Concept', 'Vervallen'])])

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


class Verordening_Structuur(Resource):

    def get(self, verordeningstructuur_uuid=None):
        params = []
        filters = request.args
        if filters and verordeningstructuur_uuid:
            return {'message': 'Filters en UUID kunnen niet gecombineerd worden'}, 400
        query = "SELECT * FROM VerordeningStructuur"
        if verordeningstructuur_uuid:
            query += "WHERE UUID=?"
            params.append(verordeningstructuur_uuid)
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
            cursor = connection.cursor()
            try:
                cursor.execute(query, *params)
            except pyodbc.IntegrityError as e:
                pattern = re.compile(r'FK_\w+_(\w+)')
                match = pattern.search(e.args[-1]).group(1)
                if match:
                    return {'message': f'Database integriteitsfout, een identifier naar een "{match}" object is niet geldig'}, 404
                else:
                    return {'message': 'Database integriteitsfout'}, 404
            except pyodbc.DatabaseError as e:
                return {'message': f'Database fout, neem contact op met de systeembeheerder Exception:[{e}]'}, 500
            for row in cursor:
                rows.append(row)
        results = []
        for row in rows:
            row = row_to_dict(row)
            # parsedrow = Verordening_Structuur_Schema().load(row)
            # parsedrow['Structuur'] = Tree_Node().dump(parse_schema_from_xml(row['Structuur']))
            tree = Tree_Node().load(parse_schema_from_xml(row['Structuur']))
            row['Structuur'] = tree
            parsedrow = Verordening_Structuur_Schema().dump(row)
            # parsedrow['Structuur'] = tree


            results.append(parsedrow)
            # row['Structuur'] = Tree_Node().dump(Tree_Node().load(parse_schema_from_xml(row['Structuur'])))
            # print(row['Structuur'])
            # print(type(row['Structuur']))
            # # raise
            # results.append(Verordening_Structuur_Schema().dump(row))
        # return Verordening_Structuur_Schema().dump(results, many=True)
        return results

        # struct = parse_schema_from_xml(sampletree)
        # parsedtree = Tree_Node().load(struct)
        # return serialize_schema_to_xml(parsedtree)
        # # return [Tree_Node().dump(Tree_Node().load(struct)),
