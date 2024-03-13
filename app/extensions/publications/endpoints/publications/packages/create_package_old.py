#             # Save state and new objects in DB
#             state_exported = json.loads(dso_service.get_filtered_export_state())
#             db.add(
#                 PublicationPackageExportState(
#                     UUID=uuid.uuid4(),
#                     Created_Date=datetime.utcnow(),
#                     Package_UUID=package.UUID,
#                     Export_Data=state_exported,
#                 )
#             )

#             # # Store new OW objects from DSO module in DB
#             # if new_package_db.Package_Event_Type == PackageType.PUBLICATION and bill_db.Is_Official:
#             #     exported_ow_objects, exported_assoc_tables = create_ow_objects_from_json(
#             #         exported_state=state_exported,
#             #         bill_type=bill.Procedure_Type,
#             #     )
#             #     # generated OW ids by DSO module
#             #     ow_ids = [ow_object.OW_ID for ow_object in exported_ow_objects]

#             #     # Query for re-used OW objects
#             #     stmt = select(OWObjectTable).where(OWObjectTable.OW_ID.in_(ow_ids))
#             #     existing_ow_objects = db.execute(stmt).scalars().all()
#             #     existing_ow_map = {ow_object.OW_ID: ow_object for ow_object in existing_ow_objects}

#             #     for ow_object in list(exported_ow_objects):
#             #         if ow_object.OW_ID in existing_ow_map:
#             #             # OW obj already exists so just add this package as relation
#             #             existing_ow_map[ow_object.OW_ID].Packages.append(new_package_db)
#             #         else:
#             #             # new OW object
#             #             ow_object.Packages.append(new_package_db)
#             #             db.add(ow_object)

#             #     # Add the OW assoc relations
#             #     db.add_all(exported_assoc_tables)

#             #     # Ensure any duplicate OW objects that were auto added by the ORM
#             #     # are removed from the session.new state
#             #     for obj in db.new:
#             #         if isinstance(obj, OWObjectTable):
#             #             if obj.OW_ID in existing_ow_map:
#             #                 db.expunge(obj)

#             # Lock the bill
#             bill_db.Locked = True
#             db.add(bill_db)

#             db.commit()

#             return PublicationPackage.from_orm(new_package_db)
