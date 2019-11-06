import marshmallow as MM
from flask import request
from flask_restful import Resource
import pyodbc
from flask_jwt_extended import get_jwt_identity
from globals import db_connection_settings, db_connection_string
from xml.etree import ElementTree as ET


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
    Structuur = MM.fields.Nested(Tree_Node, many=True)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.UUID(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.UUID(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Vigerend', 'Concept', 'Vervallen'])])

    class Meta:
        ordered = True


sampletree = '''<?xml version="1.0"?>
<tree xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns="Verordening_Tree">
    <uuid>481dccbd-366a-4a55-8efc-af878fd68b9a</uuid>
    <child>
        <uuid>7e785bd2-5822-4f14-ac1b-f437346f980c</uuid>
    </child>
    <child>
        <uuid>1540a0c5-4fee-435c-a1cf-81eefba0f241</uuid>
        <child>
            <uuid>8cd7fc14-b3fb-4aa2-a33e-d1923787d10a</uuid>
        </child>
        <child>
            <uuid>d900a8cb-151b-4420-973d-a6095f04322b</uuid>
        </child>
    </child>
</tree>
'''


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
    if remove_namespace(structure.tag) != 'tree': return None
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


class Verordening_Structuur(Resource):

    def get(self, verordeningstructuur_uuid=None):
        struct = parse_schema_from_xml(sampletree)
        parsedtree = Tree_Node().load(struct)
        return serialize_schema_to_xml(parsedtree)
        # return [Tree_Node().dump(Tree_Node().load(struct)),
