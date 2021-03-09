# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from typing import Mapping
from marshmallow.fields import Integer, String
import marshmallow as MM
from diff_match_patch import diff_match_patch
from copy import deepcopy

def diff_text_toHTML(old, new):
    """
    Generate HTML representing the changes between two pieces of text
    """
    # None should always be empty string
    old = old or ""
    new = new or ""
    diff_maker = diff_match_patch()
    diffs = diff_maker.diff_main(old, new)
    diff_maker.diff_cleanupSemantic(diffs)
    result = ""
    for (op, data) in diffs:
        if op == 1:
            result += '''<div class='revision-insert'>''' + data + '''</div>'''
        if op == -1:
            result += '''<div class='revision-removal'>''' + data + '''</div>'''
        if op == 0:
            result += data
    return result

def diff_lists(old, new):
    """
    Compare two lists and show how the new changed from the old
    """
    return {
        'new':[item for item in new if item not in old],
        'removed':[item for item in old if item not in new],
        'same':[item for item in new if item in old]
    }
    

def compare_objects(schema, old, new):
    """
    Compares two mappings (dicts), showing the changes inline 
    """
    if old.keys() != new.keys():
        raise KeyError('Objects to compare do not share same keys')

    changes = deepcopy(new)
    fields = schema.fields
    for field in fields:
        if type(fields[field]) == MM.fields.String:
            changes[field] = diff_text_toHTML(old[field], new[field])
        
        elif type(fields[field]) == MM.fields.UUID:
            continue
            
        elif type(fields[field]) == MM.fields.Integer:
            continue

        elif type(fields[field]) == MM.fields.DateTime:
            continue
        
        elif type(fields[field]) == MM.fields.Method:
            continue

        elif type(fields[field]) == MM.fields.Nested:
            changes[field] = diff_lists(old[field], new[field])
    return changes
        
