# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

"""
Tests that perform checks on comparison functions.
"""

import os
import pytest
import Endpoints.comparison


def test_simple_list():
    old_list = [1,2,3]
    new_list = [1,4,5,6]
    assert Endpoints.comparison.diff_lists(old_list, new_list) == {
        'new':[4,5,6],
        'removed':[2,3],
        'same':[1]
    }

def test_empty_list():
    old_list = [1,2,3]
    new_list = []
    assert Endpoints.comparison.diff_lists(old_list, new_list) == {
        'new':[],
        'removed':[1,2,3],
        'same':[]
    }