# from dso.services.ow.imow_waardelijsten import TypeGebiedsaanwijzingEnum as AreaDesignationTypes
# from dso.services.ow.imow_waardelijsten import get_groep_options_for_gebiedsaanwijzing_type


# AreaDesignationTypeEnum = Enum("AreaDesignationTypeEnum", {member.name: member.name for member in AreaDesignationTypes})


# class AreaDesignationValueList(BaseModel):
#     Allowed_Values: List[str]


# def get_area_designation_groups_endpoint(
#     type: AreaDesignationTypeEnum,
# ) -> AreaDesignationValueList:
#     enum_member: AreaDesignationTypes = AreaDesignationTypes[type.name]
#     group_options: Optional[List[str]] = get_groep_options_for_gebiedsaanwijzing_type(enum_member)
#     if group_options is None:
#         raise HTTPException(
#             status.HTTP_400_BAD_REQUEST,
#             f"Group options not found for area designation type {type.name}",
#         )
#     return AreaDesignationValueList(Allowed_Values=group_options)


def get_area_designation_groups_endpoint():
    pass
