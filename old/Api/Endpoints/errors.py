# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

""" 
This file contains all error handling logic for endpoints
"""
import re

check_errors = {
    "CK_InstallatieNaamExists": "Er bestaat al een actieve installatie met deze naam voor dit bedrijf.",
    "Check_Installaties_Contouren": "Dit Contour bestaat niet.",
    "Check_Installaties_Bedrijf": "Dit Bedrijf bestaat niet.",
    "check_Bedrijven_Contouren": "Dit Contour bestaat niet.",
    "check_Activiteiten_ActiviteitenCategorieen": "Deze Categorie bestaat niet.",
    "check_Activiteiten_Bedrijven": "Dit bedrijf bestaat niet.",
    "check_Activiteiten_Contouren": "Dit Contour bestaat niet.",
    "Check_Installaties_InstallatieTypes": "Dit Installatietype bestaat niet.",
    "CK_Besluiten_Bedrijf": "Dit Bedrijf bestaat niet.",
    "Check_Activiteiten_Installaties_Activiteit": "Deze Activiteit bestaat niet.",
    "Check_Activiteiten_Installaties_Installatie": "Deze Installatie bestaat niet.",
    "CK__Vergunningen_Bedrijf": "Dit bedrijf bestaat niet.",
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
    return {
        "message": f"Database error [{code}] during handling of request",
        "detailed": str(odbc_ex),
    }, 500


def handle_integrity_exception(int_ex):
    message = int_ex.args[1]
    error = determine_error(message)
    if error:
        return {"message": f"Database integrity error: {error}"}, 400
    else:
        return {"message": f"Database integrity error: {message}"}, 500


def handle_validation_exception(val_ex):
    return {
        "message": f"Validation errors",
        "errors": val_ex.normalized_messages(),
    }, 400


def handle_empty():
    return {"message": "Request data empty"}, 400


def handle_read_only():
    return {"message": "This endpoint is read-only"}, 403


def handle_no_status():
    return {"message": "This object does not have a status configuration"}, 403


def handle_UUID_does_not_exists(uuid):
    return {"message": f"Object with UUID {uuid} does not exist."}, 404


def handle_ID_does_not_exists(id):
    return {"message": f"Object with ID {id} does not exist."}, 404


def handle_validation_filter_exception(val_ex):
    return {
        "message": f"Validation errors in filters",
        "errors": val_ex.normalized_messages(),
    }, 400


def handle_queryarg_exception(val_ex):
    return {"message": str(val_ex)}, 400


def handle_empty_patch():
    return {"message": "Patching does not result in any changes."}, 400
