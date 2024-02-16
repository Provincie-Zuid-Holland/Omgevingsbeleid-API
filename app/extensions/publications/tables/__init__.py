from .ow import (
    OWAmbtsgebiedTable,
    OWDivisieTable,
    OWDivisietekstTable,
    OWGebiedenGroepTable,
    OWGebiedTable,
    OWLocationTable,
    OWObjectTable,
    OWRegelingsgebiedTable,
    OWTekstdeelTable,
)
from .tables import (
    DSOStateExportTable,
    PublicationBillTable,
    PublicationConfigTable,
    PublicationFRBRTable,
    PublicationPackageReportTable,
    PublicationPackageTable,
    PublicationTable,
)

# TODO: ensure OW objects have their DSO status updated based on LVBB report
# def update_ow_objects_status(target, value, oldvalue, initiator):
#     if get_history(target, 'Validation_Status').has_changes():
#         if value == ValidationStatusType.VALID.value:
#             for ow_object in target.OW_Objects:
#                 ow_object.DSO_Status = "Accepted"

# event.listen(PublicationPackageTable.Validation_Status, 'set', update_ow_objects_status)
