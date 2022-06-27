from typing import List, TypeVar
from diff_match_patch import diff_match_patch
from copy import deepcopy
from pydantic import BaseModel
import re

from app.db.base_class import Base

K = TypeVar("K", bound=Base)
V = TypeVar("V", bound=BaseModel)


class Comparator:
    def __init__(self, schema: V, old: K, new: K) -> None:
        self.old = old.__dict__
        self.new = new.__dict__

        if self.old.keys() != self.new.keys():
            raise KeyError("Objects to compare do not share same keys")

        # Ensure only comparable attrs/keys are used
        self.fields = self._get_comparable_fields(schema, self.old)

        # Copy to which results are written
        self.changes = deepcopy(self.old)

    def compare_objects(self) -> dict:
        """
        Compares two mappings (dicts), showing the changes inline
        """
        for attr, field in self.fields.items():
            if field.type_ == str:
                self.changes[attr] = self._diff_text_toHTML(
                    self.old[attr], self.new[attr]
                )
            elif field.type_ == List:
                self.changes[attr] = self._diff_lists(self.old[attr], self.new[attr])
            else:
                continue

        return self.changes

    def _get_comparable_fields(self, schema: V, obj: dict):
        """
        Diff pydantic schema keys vs Model keys and
        return fields comparable for changes
        """
        fields = deepcopy(schema.__fields__)

        model_diff = set(schema.__fields__.keys())
        model_diff.difference_update(set(obj.keys()))

        for diff in model_diff:
            fields.pop(diff)

        print(fields)
        return fields

    def _diff_text_toHTML(self, old: str, new: str) -> str:
        """
        Generate HTML representing the changes between two pieces of text
        """
        # None should always be empty string
        old = old or ""
        new = new or ""

        tag_map = self._generate_html_tags_maps(old, new)

        old = self._replace_tags(old, tag_map)
        new = self._replace_tags(new, tag_map)

        self._generate_html_tags_maps(old, new)

        diff_maker = diff_match_patch()
        diffs = diff_maker.diff_main(old, new)
        diff_maker.diff_cleanupSemantic(diffs)

        result = ""
        for (op, data) in diffs:
            data = self._restore_tags(data, tag_map)
            if op == 1:
                result += """<div class='revision-insert'>""" + data + """</div>"""
            if op == -1:
                result += """<div class='revision-removal'>""" + data + """</div>"""
            if op == 0:
                result += data

        return result

    def _generate_html_tags_maps(self, text1: str, text2: str) -> dict:
        mapping = dict()
        pat = re.compile(r"""</?.+?>""")
        tags = set(re.findall(pat, text1) + re.findall(pat, text2))
        repl_gen = self._random_unicode(text1 + text2)
        for tag in tags:
            mapping[tag] = next(repl_gen)

        return mapping

    def _random_unicode(self, text: str):
        all_ords = set(map(ord, text))
        possible_ords = [repl for repl in range(0, 1114111) if ord not in all_ords]
        for repl in possible_ords:
            yield chr(repl)

    def _replace_tags(self, text: str, map: dict):
        for tag, repl in map.items():
            text = text.replace(tag, repl)

        return text

    def _restore_tags(self, text: str, map: dict):
        for tag, repl in map.items():
            text = text.replace(repl, tag)

        return text

    def _diff_lists(self, old: List, new: List) -> dict:
        """
        Compare two lists and show how the new changed from the old
        """
        return {
            "new": [item for item in new if item not in old],
            "removed": [item for item in old if item not in new],
            "same": [item for item in new if item in old],
        }
