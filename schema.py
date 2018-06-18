import graphene
from graphene import ObjectType, Schema
import records
from graphql import GraphQLError
import pyodbc

from validators import *
from queries import *
from helpers import single_object_by_uuid, objects_from_query, related_objects_from_query
from globals import db_connection_string, db_connection_settings


class Ambitie(graphene.ObjectType):
    UUID = graphene.UUID()
    Titel = graphene.String(description="Titel van deze Ambitie")
    Omschrijving = graphene.String(description="Omschrijving van deze Ambitie")
    Weblink = graphene.String(description="Weblink van deze Ambitie")
    Begin_Geldigheid = graphene.types.datetime.DateTime(
        description="Begindatum van de geldigheid van deze Ambitie")
    Eind_Geldigheid = graphene.types.datetime.DateTime(
        description="Einddatum van de geldigheid van deze Ambitie")
    Created_By = graphene.String(description="Eigenaar van deze Ambitie")
    Created_Date = graphene.types.datetime.DateTime(
        description="Datum waarop deze Ambitie aangemaakt is")
    Modified_By = graphene.String(description="Aanpasser van deze Ambitie")
    Modified_Date = graphene.types.datetime.DateTime(
        description="Datum waarop deze Ambitie aangepast is")


class AmbitieQueries(graphene.ObjectType):
    ambities = graphene.List(Ambitie)
    ambitie = graphene.Field(Ambitie, uuid=graphene.UUID(required=True))
    resolve_ambities = objects_from_query('Ambities', alle_ambities)
    resolve_ambitie = single_object_by_uuid('Ambitie', ambitie_op_uuid)


# Ambitie mutations

class AmbitieInput(graphene.InputObjectType):
    Titel = graphene.String()
    Omschrijving = graphene.String()
    Weblink = graphene.String()
    Begin_Geldigheid = graphene.types.datetime.DateTime()
    Eind_Geldigheid = graphene.types.datetime.DateTime()
    Created_By = graphene.String()

class CreateAmbitie(graphene.Mutation):
    class Arguments():
        ambitie_data = AmbitieInput()

    ok = graphene.Boolean()
    Ambitie_Uuid = graphene.UUID()

    def mutate(self, info, ambitie_data=None):
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
            '''
            INSERT INTO Ambities (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By)
            OUTPUT inserted.UUID
            VALUES (?, ?, ?, ?, ?, ?); 
            ''', 
            ambitie_data.Titel,
            ambitie_data.Omschrijving,
            ambitie_data.Weblink,
            ambitie_data.Begin_Geldigheid,
            ambitie_data.Eind_Geldigheid,
            ambitie_data.Created_By)
        new_uuid = cursor.fetchone()[0]
        connection.commit()
        return CreateAmbitie(ok=True, Ambitie_Uuid=new_uuid)
        


# Mutation queries


class Mutations(graphene.ObjectType):
    create_ambitie = CreateAmbitie.Field()

# Hoofdquery


class Query(AmbitieQueries):
    class meta:
        name = "Root query"


Schema = Schema(query=Query, mutation=Mutations)
