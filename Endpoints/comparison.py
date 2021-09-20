# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from typing import Mapping
from marshmallow.fields import Integer, String
import marshmallow as MM
from diff_match_patch import diff_match_patch
from copy import deepcopy
import random
import re

# The functions below apply a 'trick' to the diffing.
# By replacing every HTML tag with a random unicode symbol that is not already in the text, 
# doing the diff and then restoring the tags we can't get tag collisions

# Idea from https://github.com/google/diff-match-patch/wiki/Plain-Text-vs.-Structured-Content


def random_unicode(text):
    while True:
        rand = random.randint(0, 1000000)
        char = chr(rand)
        if char not in text:
            return char


def generate_html_tags_maps(text1, text2):
    mapping = {}
    pat = re.compile(r"""</?.+?>""")
    tags = set(re.findall(pat, text1) + re.findall(pat, text2))
    all_text = text1 + text2
    for tag in tags:
        mapping[tag] = random_unicode(all_text)

    return mapping


def replace_tags(text, map):
    for tag, repl in map.items():
        text = text.replace(tag, repl)
    return text


def restore_tags(text, map):
    for tag, repl in map.items():
        text = text.replace(repl, tag)
    return text


def diff_text_toHTML(old, new):
    """
    Generate HTML representing the changes between two pieces of text
    """
    # None should always be empty string
    old = old or ""
    new = new or ""
    tag_map = generate_html_tags_maps(old, new)
    old = replace_tags(old, tag_map)
    new = replace_tags(new, tag_map)
    generate_html_tags_maps(old, new)
    diff_maker = diff_match_patch()
    diffs = diff_maker.diff_main(old, new)
    diff_maker.diff_cleanupSemantic(diffs)
    result = ""
    for (op, data) in diffs:
        data = restore_tags(data, tag_map)
        if op == 1:
            result += """<div class='revision-insert'>""" + data + """</div>"""
        if op == -1:
            result += """<div class='revision-removal'>""" + data + """</div>"""
        if op == 0:
            result += data
    return result


def diff_lists(old, new):
    """
    Compare two lists and show how the new changed from the old
    """
    return {
        "new": [item for item in new if item not in old],
        "removed": [item for item in old if item not in new],
        "same": [item for item in new if item in old],
    }


def compare_objects(schema, old, new):
    """
    Compares two mappings (dicts), showing the changes inline
    """
    if old.keys() != new.keys():
        raise KeyError("Objects to compare do not share same keys")

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
