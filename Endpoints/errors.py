# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

""" 
This file contains all error handling logic for endpoints
"""
import re

check_errors = {
    "CK_InstallatieNaamExists" : "Er bestaat al een actieve installatie met deze naam voor dit bedrijf.",
    "Check_Installaties_Contouren": "Dit Contour bestaat niet.",
    "Check_Installaties_Bedrijf": "Dit Bedrijf bestaat niet.",
    "check_Bedrijven_Contouren": "Dit Contour bestaat niet.",
    "check_Activiteiten_ActiviteitenCategorieen":  "Deze Categorie bestaat niet.",
    "check_Activiteiten_Bedrijven": "Dit bedrijf bestaat niet.",
    "check_Activiteiten_Contouren": "Dit Contour bestaat niet.",
    "Check_Installaties_InstallatieTypes" : "Dit Installatietype bestaat niet.",
    "CK_Besluiten_Bedrijf": "Dit Bedrijf bestaat niet.",
    "Check_Activiteiten_Installaties_Activiteit": "Deze Activiteit bestaat niet.",
    "Check_Activiteiten_Installaties_Installatie": "Deze Installatie bestaat niet.",
    "CK__Vergunningen_Bedrijf": "Dit bedrijf bestaat niet."
}

def determine_error(message):
    """
    Try to find registered Check Constraints in order to provide better error messages.
    """
    for error in check_errors:
        expr = re.compile(error)
        if re.search(expr, message):
            return check_errors[error]
    return None

def handle_odbc_exception(odbc_ex):
    code = odbc_ex.args[0]
    return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}, 500

def handle_integrity_exception(int_ex):
    message = int_ex.args[1]
    error = determine_error(message)
    if error:
        return {"message": f"Database integrity error: {error}"}, 400
    else:
        return {"message": f"Database integrity error: {message}"}, 500

def handle_validation_exception(val_ex):
    return val_ex.normalized_messages(), 400