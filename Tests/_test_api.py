# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland


import os
import pytest
import pyodbc
import copy
import datetime
from flask import jsonify
from re import A

from Api.Models import (
    beleidskeuzes,
    ambities,
    beleidsrelaties,
    maatregelen,
    belangen,
    beleidsprestaties,
    beleidsmodule,
)
from Api.settings import null_uuid
from Api.datamodel import endpoints
from Api.settings import min_datetime, max_datetime
from Endpoints.references import (
    UUID_List_Reference,
)

from Api.Tests.test_data import generate_data, reference_rich_beleidskeuze



