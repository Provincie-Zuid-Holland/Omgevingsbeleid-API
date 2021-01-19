# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import datamodel
import json
from flask import Flask, jsonify, request
import os
import marshmallow as MM

def render_spec():
    with open(os.path.join(os.getcwd(), 'Spec/basespec.json'), 'r') as basefile:
        base_spec = json.loads(basefile.read())
        for model in datamodel.endpoints:
            properties = {}
            fields = model.read_schema().fields
            for field in fields:
                    if type(fields[field]) == MM.fields.String:
                        properties[field] = {
                            'description': 'None',
                            'type': 'string'
                        }
                    
                    elif type(fields[field]) == MM.fields.UUID:
                         properties[field] = {
                            'description': 'None',
                            'type': 'string',
                            'format': 'uuid'
                        }
                    
                    elif type(fields[field]) == MM.fields.Integer:
                        properties[field] = {
                            'description': 'None',
                            'type': 'integer'
                        }

                    elif type(fields[field]) == MM.fields.DateTime:
                        properties[field] = {
                            'description': 'None',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    
                    elif type(fields[field]) == MM.fields.Method:
                        properties[field] = {
                            'description': 'Not implemented',
                            'type': 'string'
                        }

                    elif type(fields[field]) == MM.fields.Nested:
                        properties[field] = {
                            'description': 'A nested field',
                            'type': 'string',
                            'format': 'uuid'
                        }

            base_spec['components']['schemas'][model.slug] = {'properties': properties}
    return base_spec


def specView():
    return jsonify(render_spec())
