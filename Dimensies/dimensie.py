from flask_restful import Resource
import records
import pyodbc
from flask import request

from globals import db_connection_string, db_connection_settings

class Dimensie(Resource):
    """Een algemene dimensie"""
    def __init__(self, tableschema, tablename_all, tablename_actueel=None):
        # super().__init__() 
        self._tablename_all = tablename_all
        
        if tablename_actueel:
            self._tablename_actueel = tablename_actueel
        else:
            self._tablename_actueel = tablename_all
        
        self._tableschema = tableschema
        self.uuid_query = f'SELECT * FROM {tablename_all} WHERE UUID=:uuid'
        self.all_query = f'SELECT * FROM {tablename_actueel}'
        

    def single_object_by_uuid(self, uuid):
        """
        Verkrijg een enkel object op basis van UUID
        """
        db = records.Database(db_connection_string)
        return db.query(self.uuid_query, uuid=uuid).first()
    
    def objects_from_query(self):
        """
        Verkrijg alle objecten uit een table
        """
        db = records.Database(db_connection_string)
        return db.query(self.all_query)


    def get(self, uuid=None):
        """
        GET endpoint voor deze dimensie
        """
        if uuid:
            dimensie_object = self.single_object_by_uuid(uuid)        
            
            if not dimensie_object:
                return {'message': f"Object met identifier {uuid} is niet gevonden in table {self._tablename_all}"}, 404
            
            schema = self._tableschema()
            return(schema.dump(dimensie_object))
        else:    
            dimensie_objecten = self.objects_from_query()
            
            schema = self._tableschema()
            return(schema.dump(dimensie_objecten, many=True))
            

    # def post(self, ambitie_uuid=None):
    #     if ambitie_uuid:
    #         return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
    #     schema = Ambitie_Schema(
    #         exclude = ('UUID','Modified_By', 'Modified_Date'),
    #         unknown=MM.utils.RAISE)
    #     try:
    #         ambitie = schema.load(request.get_json())
    #     except MM.exceptions.ValidationError as err:
    #         return err.normalized_messages(), 400
    #     connection = pyodbc.connect(db_connection_settings)
    #     cursor = connection.cursor()
    #     cursor.execute(ambitie_aanmaken,
    #     ambitie['Titel'],
    #     ambitie['Omschrijving'],
    #     ambitie['Weblink'],
    #     ambitie['Begin_Geldigheid'],
    #     ambitie['Eind_Geldigheid'],
    #     ambitie['Created_By'],
    #     ambitie['Created_Date'],
    #     ambitie['Created_By'],
    #     ambitie['Created_Date'])
    #     new_uuid = cursor.fetchone()[0]
        
    #     connection.commit()
    #     return {"Resultaat_UUID": f"{new_uuid}"}
    
    # def patch(self, ambitie_uuid=None):
    #     if not ambitie_uuid:
    #         return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
    #     patch_schema = Ambitie_Schema(
    #         partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
    #         exclude = ('UUID', 'Created_By', 'Created_Date'),
    #         unknown=MM.utils.RAISE
    #         )
    #     try:
    #         ambitie_aanpassingen = patch_schema.load(request.get_json())
    #     except MM.exceptions.ValidationError as err:
    #         return err.normalized_messages(), 400    

    #     oude_ambitie = single_object_by_uuid('Ambities', ambitie_op_uuid, uuid=ambitie_uuid)
            
    #     if not oude_ambitie:
    #         return {'message': f"Ambitie met UUID {ambitie_uuid} is niet gevonden"}, 404
            
    #     ambitie = {**oude_ambitie, **ambitie_aanpassingen}
        
    #     connection = pyodbc.connect(db_connection_settings)
    #     cursor = connection.cursor()
    #     cursor.execute(ambitie_aanpassen,
    #     ambitie['ID'],
    #     ambitie['Titel'],
    #     ambitie['Omschrijving'],
    #     ambitie['Weblink'],
    #     ambitie['Begin_Geldigheid'],
    #     ambitie['Eind_Geldigheid'],
    #     ambitie['Created_By'],
    #     ambitie['Created_Date'],
    #     ambitie['Modified_By'],
    #     ambitie['Modified_Date'])
    #     ambitie_uuid = cursor.fetchone()[0]
        
    #     connection.commit()
    #     return {"Resultaat_UUID": f"{ambitie_uuid}"}


