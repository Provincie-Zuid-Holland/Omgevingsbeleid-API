from unittest.mock import Mock

from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingType


def make_gebiedsaanwijzing(deprecated: bool) -> Mock | Gebiedsaanwijzing:
    aanwijzing_type: Mock | GebiedsaanwijzingType = Mock(GebiedsaanwijzingType)
    aanwijzing_type.deprecated = deprecated
    gebiedsaanwijzing: Mock | Gebiedsaanwijzing = Mock(Gebiedsaanwijzing)
    gebiedsaanwijzing.aanwijzing_type = aanwijzing_type
    return gebiedsaanwijzing
