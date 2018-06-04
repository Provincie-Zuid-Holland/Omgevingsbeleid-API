import graphene
from graphene import ObjectType, Schema
import records
from helpers import get_single_result
from graphql import GraphQLError
from validators import *


# Thema objects

class Thema(graphene.ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van het thema")
    beschrijving = graphene.String(description="Beschrijving van het thema")
    opgaven = graphene.List(
        lambda: Opgave, description="Opgaven die bij dit thema horen")

    def resolve_opgaven(self, info, **kwards):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from opgaven where thema=:id', id=self.id)
        return results


class ThemaQueries(graphene.ObjectType):
    themas = graphene.List(Thema)
    thema = graphene.Field(lambda: Thema, id=graphene.Int(required=True))

    def resolve_thema(root, info, **kwargs):
        id = kwargs.get('id')

        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas where id=:id',
                           id=id)
        return results.first(
            default=GraphQLError(f'Thema met id {id} is niet gevonden'))

    def resolve_themas(root, info):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas')
        return results


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
            raise GraphQLError(themaValidator.errors)


# Opgave objects

class Opgave(graphene.ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van de opgave")
    beschrijving = graphene.String(description="Beschrijving van de opgave")
    thema = graphene.Field(
        Thema, description="Thema's waar deze opgave bij hoort")

    def resolve_thema(self, info, **kwargs):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas where id=:id',
                           id=self.thema)
        return results.first()


class OpgaveQueries(graphene.ObjectType):
    opgaven = graphene.List(Opgave)
    opgave = graphene.Field(Opgave, id=graphene.Int(required=True))

    def resolve_opgave(root, info, **kwargs):
        id = kwargs.get('id')

        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from opgaven where id=:id',
                           id=id)
        single_result = results.first()
        if single_result:
            return single_result
        else:
            raise GraphQLError(f'Opgave met id {id} is niet gevonden')

    def resolve_opgaven(root, info):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from opgaven')
        return results

# Mutation queries


class Mutations(graphene.ObjectType):
    create_thema = CreateThema.Field()

# Hoofdquery


class Query(ThemaQueries, OpgaveQueries):
    class meta:
        name = "Root query"


Schema = Schema(query=Query, mutation=Mutations)
