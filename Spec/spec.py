# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from typing import DefaultDict
import datamodel
import json
from flask import Flask, jsonify, request
import os
import marshmallow as MM
from Endpoints import references


def render_spec():
    with open(os.path.join(os.getcwd(), 'Spec/basespec.json'), 'r') as basefile:
        base_spec = json.loads(basefile.read())

        base_spec['components']['schemas'] = render_schemas(
            datamodel.endpoints)
        base_spec['components']['securitySchemes'] = {'bearerAuth': {
            'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}}
        base_spec['paths'] = render_paths(datamodel.endpoints)
        return base_spec


def render_schemas(endpoints):
    schemas = {}
    schemas['list_reference'] = {
        'properties': {
            'UUID': {
                'type': 'string',
                'format': 'uuid'
            },
            'Koppeling_Omschrijving': {
                'type': 'string'
            },
        }
    }
    for model in endpoints:
        read_properties = {}
        write_properties = {}
        change_properties = {}
        fields = model().fields
        for field in fields:

            # Nested field
            if type(fields[field]) == MM.fields.Nested:
                ref = model.Meta.references[field]
                slug = ref.schema.Meta.slug
                if isinstance(ref, references.UUID_Reference):
                    read_properties[field] = {
                        'description': f'An inlined {slug} object',
                        '$ref': f'#/components/schemas/{slug}_read'
                    }
                    write_properties[field] = {
                        'description': f'A UUID reference to a {slug} object',
                        'type': 'string',
                        'format': 'uuid'
                    }
                if isinstance(ref, references.UUID_List_Reference):
                    read_properties[field] = {
                        'description': f'An list of {slug} objects',
                        'type': 'array',
                        'items': {
                            '$ref': f'#/components/schemas/{slug}-read'}
                    }
                    write_properties[field] = {
                        'description': f'An list of references to {slug} objects',
                        'type': 'array',
                        'items': {
                            '$ref': f'#/components/schemas/list_reference'}
                    }
                    change_properties[field] = {
                        'description': f'An object that shows the changges in the list',
                        'type': 'object',
                        'properties': {
                            'new': {
                                'type': 'array',
                                'items': {
                                    '$ref': f'#/components/schemas/{slug}-read'}
                            },
                            'removed': {
                                'type': 'array',
                                'items': {
                                    '$ref': f'#/components/schemas/{slug}-read'}
                            },
                            'same': {
                                'type': 'array',
                                'items': {
                                    '$ref': f'#/components/schemas/{slug}-read'}
                            }
                        }
                    }
            # Simple field
            else:
                props = {}

                if type(fields[field]) == MM.fields.String:
                    props = {
                        'description': 'None',
                        'type': 'string'
                    }

                elif type(fields[field]) == MM.fields.UUID:
                    props = {
                        'description': 'None',
                        'type': 'string',
                        'format': 'uuid'
                    }

                elif type(fields[field]) == MM.fields.Integer:
                    props = {
                        'description': 'None',
                        'type': 'integer'
                    }

                elif type(fields[field]) == MM.fields.DateTime:
                    props = {
                        'description': 'None',
                        'type': 'string',
                        'format': 'date-time'
                    }

                elif type(fields[field]) == MM.fields.Method:
                    props = {
                        'description': 'Not implemented',
                        'type': 'string'
                    }

                # add enums
                if fields[field].validate:
                    try:
                        props['enum'] = fields[field].validate.choices
                    except AttributeError:
                        pass

                # Check if the field was processed
                if not props:
                    fieldtype = type(fields[field])
                    raise(NotImplementedError(
                        f'Unable to generate spec for {fieldtype} field'))

                read_properties[field] = props
                change_properties[field] = props
                if not ('excluded_post' in fields[field].metadata['obprops'] and 'excluded_patch' in fields[field].metadata['obprops']):
                    write_properties[field] = props

        schemas[model.Meta.slug+"-read"] = {'description': f'Schema that defines the structure of {model.Meta.slug} when reading',
                                            'properties': read_properties}

        schemas[model.Meta.slug+"-change"] = {'description': f'Schema that defines the structure of {model.Meta.slug} when looking at changes',
                                              'properties': change_properties}
        schemas[model.Meta.slug+"-write"] = {
            'description': f'Schema that defines how to write {model.Meta.slug}', 'properties': write_properties}

    return schemas


def render_paths(endpoints):
    paths = {}
    paths = DefaultDict(dict)
    for model in endpoints:
        paths[f'/{model.Meta.slug}']['get'] = {
            'parameters': [{
                'name': 'filters',
                'in': 'query',
                'description': 'Filters to apply to the selection, represented by a comma-seperated list of pairs. The pairs are delimited by a : symbol.',
                'required': False,
                'example': 'Status:Vigerend,ID:1',
                'schema': {
                    'type': 'string'
                }
            },
                {
                'name': 'limit',
                'in': 'query',
                'description': 'Amount of objects to maximally retrieve',
                'required': False,
                'schema': {
                    'type': 'integer',
                    'minimum': 0
                }
            },
                {
                'name': 'offset',
                'in': 'query',
                'description': 'The amound of objects to skip',
                'required': False,
                'schema': {
                    'type': 'integer',
                    'minimum': 0
                }
            }],
            'summary': f'Gets all the {model.Meta.slug} lineages and shows the latests object for each',
            'responses': {
                '400': {
                    'description': 'Invalid filter provided',
                    'content': {
                        'application/json': {
                            'schema':
                            {'properties': {
                                'message': {
                                    'type': 'string',
                                    'description': 'A description of the invalid filters'
                                }
                            }
                            }
                        }
                    }
                },
                '200': {
                    'description': 'a list of lineages',
                    'content': {
                        'application/json': {
                            'schema':
                            {
                                'type': 'array',
                                'items': {
                                    '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                }
                            }
                        }
                    }
                }
            }
        }

        paths[f'/version/{model.Meta.slug}/{{object_uuid}}']['get'] = {
            'parameters': [{
                'name': 'object_uuid',
                'in': 'path',
                'description': 'UUID of the object to read',
                'required': True,
                'schema': {
                        'type': 'uuid'
                }
            }],
            'summary': f'Gets all the {model.Meta.slug} lineages and shows the latests object for each',
            'responses': {
                '200': {
                    'description': 'a list of lineages',
                    'content': {
                        'application/json': {
                            'schema':
                            {
                                '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                            }
                        }
                    }
                },
                '404': {
                    'description': 'Item with UUID not found',
                    'content': {
                        'application/json': {
                            'schema':
                            {'properties': {
                                'message': {
                                    'type': 'string',
                                    'description': 'A description of the error'
                                }
                            }
                            }
                        }
                    }
                }
            }
        }

        paths[f'/changes/{model.Meta.slug}/{{old_uuid}}/{{new_uuid}}']['get'] = {
            'parameters': [{
                'name': 'old_uuid',
                'in': 'path',
                'description': 'UUID of the old object to compare to',
                'required': True,
                'schema': {
                        'type': 'uuid'
                }
            }, {
                'name': 'new_uuid',
                'in': 'path',
                'description': 'UUID of the new object to compare with',
                'required': True,
                'schema': {
                        'type': 'uuid'
                }
            },
            ],
            'summary': f'Shows the changes between two versions of objects',
            'responses': {
                '200': {
                    'description': 'Compare result',
                    'content': {
                        'application/json': {
                            'schema': {
                                'properties': {
                                    'old': {
                                        '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                    },
                                    'changes': {
                                        '$ref': f'#/components/schemas/{model.Meta.slug}-change'
                                    }
                                }
                            }
                        }
                    }
                },
                '404': {
                    'description': 'UUID does not exist',
                    'content': {
                        'application/json': {
                            'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                        }
                    }
                },
                '500': {
                    'description': 'Server error',
                    'content': {
                        'application/json': {
                            'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }

                                }
                        }
                    }
                }
            }
        }

        paths[f'/{model.Meta.slug}/{{lineage_id}}']['get'] = {
            'parameters': [{
                'name': 'lineage_id',
                'in': 'path',
                'description': 'ID of the lineage to read',
                'required': True,
                'schema': {
                    'type': 'integer'
                }},
                {
                'name': 'filters',
                'in': 'query',
                'description': 'Filters to apply to the selection, represented by a comma-seperated list of pairs. The pairs are delimited by a : symbol.',
                'required': False,
                'example': 'Status:Vigerend,ID:1',
                'schema': {
                    'type': 'string'
                }},
                {
                'name': 'limit',
                'in': 'query',
                'description': 'Amount of objects to maximally retrieve',
                'required': False,
                'schema': {
                    'type': 'integer',
                    'minimum': 0
                }},
                {
                'name': 'offset',
                'in': 'query',
                'description': 'The amound of objects to skip',
                'required': False,
                'schema': {
                    'type': 'integer',
                    'minimum': 0
                }}],
            'summary': f'Gets all the {model.Meta.slug} lineages and shows the latests object for each',
            'responses': {
                '404': {
                    'description': 'Item with ID not found',
                    'content': {
                        'application/json': {
                            'schema':
                            {'properties': {
                                'message': {
                                    'type': 'string',
                                    'description': 'A description of the error'
                                }
                            }
                            }
                        }
                    }
                },
                '200': {
                    'description': 'all the objects in the lineage, ordered by "Modified_Date" descending',
                    'content': {
                        'application/json': {
                            'schema':
                            {
                                'type': 'array',
                                'items': {
                                    '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                }
                            }
                        }
                    }
                }
            }
        }

        if model.Meta.status_conf:
            paths[f'/valid/{model.Meta.slug}']['get'] = {
                'parameters': [{
                    'name': 'filters',
                    'in': 'query',
                    'description': 'Filters to apply to the selection, represented by a comma-seperated list of pairs. The pairs are delimited by a : symbol.',
                    'required': False,
                    'example': 'Status:Vigerend,ID:1',
                    'schema': {
                        'type': 'string'
                    }},
                    {
                    'name': 'limit',
                    'in': 'query',
                    'description': 'Amount of objects to maximally retrieve',
                    'required': False,
                    'schema': {
                        'type': 'integer',
                        'minimum': 0
                    }},
                    {
                    'name': 'offset',
                    'in': 'query',
                    'description': 'The amound of objects to skip',
                    'required': False,
                    'schema': {
                        'type': 'integer',
                        'minimum': 0
                    }}],
                'summary': f'Gets all the {model.Meta.slug} lineages and shows the latests valid object for each',
                'responses': {
                    '404': {
                        'description': 'The object does not exist or does not have a status field',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                            }
                        }
                    },
                    '200': {
                        'description': 'all the latests valid objects for every lineage',
                        'content': {
                            'application/json': {
                                'schema':
                                {
                                    'type': 'array',
                                    'items': {
                                        '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                    }
                                }
                            }
                        }
                    }
                }
            }

            paths[f'/valid/{model.Meta.slug}/{{lineage_id}}']['get'] = {
                'parameters': [{
                    'name': 'lineage_id',
                    'in': 'path',
                    'description': 'ID of the lineage to read',
                    'required': True,
                    'schema': {
                        'type': 'integer'
                    }
                }],
                'summary': f'Gets all the {model.Meta.slug} in this lineage that are valid',
                'responses': {
                    '404': {
                        'description': 'The object does not exist or does not have a status field',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                            }
                        }
                    },
                    '200': {
                        'description': 'all the latests valid objects for every lineage',
                        'content': {
                            'application/json': {
                                'schema':
                                {
                                    'type': 'array',
                                    'items': {
                                        '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                    }
                                }
                            }
                        }
                    }
                }
            }

        if not model.Meta.read_only:
            paths[f'/{model.Meta.slug}']['post'] = {
                'security': [{'bearerAuth': []}],
                'summary': f'Creates a new {model.Meta.slug} lineage',
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                '$ref': f'#/components/schemas/{model.Meta.slug}-write'
                            }
                        }
                    }
                },
                'responses': {
                    '201': {
                        'description': 'Lineage created',
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                }
                            }
                        }
                    },
                    '403': {
                        'description': 'Model is read only',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                            }
                        }
                    },
                    '400': {
                        'description': 'Request data empty or invalid',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                            }
                        }
                    },
                    '500': {
                        'description': 'Server error',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }

                                }
                            }
                        }
                    }
                }
            }
            paths[f'/{model.Meta.slug}/{{lineage_id}}']['patch'] = {
                'security': [{'bearerAuth': []}],
                'summary': f'Adds a new {model.Meta.slug} to a lineage',
                'parameters': [{
                    'name': 'lineage_id',
                    'in': 'path',
                    'description': 'ID of the lineage to write to',
                    'required': True,
                    'schema': {
                        'type': 'integer'
                    }
                }],
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                '$ref': f'#/components/schemas/{model.Meta.slug}-write'
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'New version created',
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': f'#/components/schemas/{model.Meta.slug}-read'
                                }
                            }
                        }
                    },
                    '403': {
                        'description': 'Model is read only',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                            }
                        }
                    },
                    '400': {
                        'description': 'Request data empty or invalid',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }
                                }
                            }
                        }
                    },
                    '500': {
                        'description': 'Server error',
                        'content': {
                            'application/json': {
                                'schema':
                                {'properties': {
                                    'message': {
                                        'type': 'string',
                                        'description': 'A description of the error'
                                    }
                                }

                                }
                            }
                        }
                    }
                }
            }
    paths[f'/search']['get'] = {
        'summary': f'Search for objects with a textual query',
        'parameters': [{
            'name': 'query',
            'in': 'query',
            'description': 'The textual query to search on',
            'required': True,
            'schema': {
                'type': 'string'
            }},
            {
            'name': 'only',
            'in': 'query',
            'description': 'Only search these objects (can not be used in combination with `exclude`',
            'required': False,
            'schema': {
                'type': 'string',
                'format': 'comma seperated list'
            }},
            {
            'name': 'exclude',
            'in': 'query',
            'description': 'Exclude these objects form search (can not be used in combination with `only`',
            'required': False,
            'schema': {
                'type': 'string',
                'format': 'comma seperated list'
            }},
            {
            'name': 'limit',
            'in': 'query',
            'description': 'Limit the amount of results',
            'required': False,
            'schema': {
                'type': 'integer'
            }}
        ],
        'responses': {
            '200': {
                'description': 'Search results',
                'content': {
                    'application/json': {
                        'schema': {
                            'properties': {
                                'Omschrijving': {
                                    'type': 'string',
                                    'description': 'A description of this object'
                                },
                                'Titel': {
                                    'type': 'string',
                                    'description': 'The title of this object'
                                },
                                'RANK': {
                                    'type': 'int',
                                    'description': 'A representation of the search rank, only usefull for comparing between two results'
                                },
                                'type': {
                                    'type': 'string',
                                    'description': 'The type of this object'
                                },
                                'UUID': {
                                    'type': 'string',
                                    'format': 'uuid',
                                    'description': 'The UUID of this object'
                                }

                            }

                        }
                    }
                }
            },
            '400': {
                'description': 'No search query provided or no objects in resultset',
                'content': {
                    'application/json': {
                        'schema':
                        {'properties': {
                            'message': {
                                'type': 'string',
                                'description': 'A description of the error'
                            }
                        }
                        }
                    }
                }
            },
            '403': {
                'description': '`Exclude` and `only` in the same query',
                'content': {
                    'application/json': {
                        'schema':
                        {'properties': {
                            'message': {
                                'type': 'string',
                                'description': 'A description of the error'
                            }
                        }
                        }
                    }
                }
            }
        }
    }
    return paths


def specView():
    return jsonify(render_spec())
