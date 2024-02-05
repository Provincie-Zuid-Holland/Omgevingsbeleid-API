class MissingPublicationConfigError(Exception):
    pass


class PublicationNotFound(Exception):
    pass


class PublicationBillNotFound(Exception):
    pass


class DSOModuleException(Exception):
    pass


class DSOStateExportError(Exception):
    pass


class DSOExportOWError(Exception):
    pass
