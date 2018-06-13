import graphene
from graphene import ObjectType, Schema
import records
from graphql import GraphQLError

from validators import *
from queries import *
from helpers import single_object_by_id, objects_from_query, related_objects_from_query
from globals import db_connection_string
# Thema objects


class Thema(graphene.ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van het thema")
    beschrijving = graphene.String(description="Beschrijving van het thema")
    opgaven = graphene.List(
        lambda: Opgave, description="Opgaven die bij dit thema horen")

    resolve_opgaven = related_objects_from_query(
        'Opgaven', alle_opgaven_bij_thema, {'id': 'id'})


class ThemaQueries(graphene.ObjectType):
    themas = graphene.List(Thema)
    thema = graphene.Field(lambda: Thema, id=graphene.Int(required=True))

    resolve_thema = single_object_by_id('Thema', thema_op_id)
    resolve_themas = objects_from_query('Themas', alle_themas)


class ThemaInput(graphene.InputObjectType):
    naam = graphene.String()
    beschrijving = graphene.String()
    opgaven = graphene.List(graphene.ID)


class CreateThema(graphene.Mutation):
    class Arguments():
        thema_data = ThemaInput()

    ok = graphene.Boolean()
    thema = graphene.Field(lambda: Thema)

    def mutate(self, info, thema_data=None):
        if themaValidator.validate(thema_data):
            db = records.Database("sqlite:///mock.db")
            db.query(
                '''INSERT INTO themas (naam, beschrijving) 
                VALUES (:naam, :beschrijving)''',
                naam=thema_data.naam, beschrijving=thema_data.beschrijving)
            result = db.query('SELECT last_insert_rowid()')
            print(list(result))
            return CreateThema(ok=True, thema=None)
        else:
            raise GraphQLError(f"Validation error: {themaValidator.errors}")


# Opgave objects

class Opgave(graphene.ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van de opgave")
    beschrijving = graphene.String(description="Beschrijving van de opgave")
    thema = graphene.List(
        lambda: Thema, description="Thema's waar deze opgave bij hoort")

    resolve_thema = related_objects_from_query(
        'Thema', alle_themas_bij_opgave, {'id': 'thema'})


class OpgaveQueries(graphene.ObjectType):
    opgaven = graphene.List(Opgave)
    opgave = graphene.Field(Opgave, id=graphene.Int(required=True))

    resolve_opgave = single_object_by_id('Opgave', opgave_op_id)
    resolve_opgaven = objects_from_query('Opgaven', alle_opgaven)


# Ambitie objects

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
    # ambitie = graphene.Field(Ambitie, uuid=graphene.UUID(required=True))
    resolve_ambities = objects_from_query('Ambities', alle_ambities)

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
    Ambitie = graphene.Field(lambda: Ambitie)

    def mutate(self, info, ambitie_data=None):
        # if themaValidator.validate(ambitie_data):
        db = records.Database(db_connection_string)
        results = db.query(
            '''INSERT INTO Ambities (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By) 
            OUTPUT Inserted.UUID
            VALUES (:Titel, :Omschrijving, :Weblink, :Begin_Geldigheid, :Eind_Geldigheid, :Created_By);''',
            Titel=ambitie_data.Titel, Omschrijving=ambitie_data.Omschrijving, Weblink=ambitie_data.Weblink,
            Begin_Geldigheid=ambitie_data.Begin_Geldigheid, Eind_Geldigheid=ambitie_data.Eind_Geldigheid,
            Created_By=ambitie_data.Created_By)
        
        # print(results.first())
        return CreateThema(ok=True)
        # else:
        #     raise GraphQLError(f"Validation error: {themaValidator.errors}")


# Mutation queries


class Mutations(graphene.ObjectType):
    create_ambitie = CreateAmbitie.Field()

# Hoofdquery


class Query(AmbitieQueries):
    class meta:
        name = "Root query"


Schema = Schema(query=Query, mutation=Mutations)
