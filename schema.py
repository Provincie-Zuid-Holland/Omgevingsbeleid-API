import graphene
from graphene import ObjectType, Schema
import records
from helpers import get_single_result
from graphql import GraphQLError

# Thema objects


class Thema(ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van het thema")
    beschrijving = graphene.String(description="Beschrijving van het thema")


class ThemaQueries(ObjectType):
    themas = graphene.List(Thema)
    thema = graphene.Field(Thema, id=graphene.Int(required=True))

    def resolve_thema(root, info, **kwargs):
        id = kwargs.get('id')

        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas where id=:id',
                           id=id)
        return results.first(default=GraphQLError(f'Thema met id {id} is niet gevonden'))

    def resolve_themas(root, info):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas')
        return results

# Opgave objects


class Opgave(ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van de opgave")
    beschrijving = graphene.String(description="Beschrijving van de opgave")
    thema = graphene.Field(
        Thema, description="Thema's waar deze opgave bij hoort")

    def resolve_thema(self, info, **kwargs):
        db = records.Database("sqlite:///mock.db")
        # print(self.thema)
        results = db.query('select * from themas where id=:id',
                           id=self.thema)
        return results.first()


class OpgaveQueries(ObjectType):
    opgaven = graphene.List(Opgave)
    opgave = graphene.Field(Opgave, id=graphene.Int(required=True))

    def resolve_opgave(root, info, **kwargs):
        id = kwargs.get('id')

        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from opgaven where id=:id',
                           id=id)
        return results.first(default=GraphQLError(f'Opgave met id {id} is niet gevonden'))

    def resolve_opgaven(root, info):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from opgaven')
        return results

# Hoofdquery


class Query(ThemaQueries, OpgaveQueries):
    class meta:
        name = "Root query"


Schema = Schema(query=Query)
