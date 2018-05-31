import graphene
from graphene import ObjectType, Schema
import records
from helpers import get_single_result
from graphql import GraphQLError

class Thema(ObjectType):
    id = graphene.ID()
    naam = graphene.String(description="Naam van het thema")
    beschrijving = graphene.String(description="Beschrijving van het thema")


class Query(ObjectType):
    all_themas = graphene.List(Thema)
    thema = graphene.Field(Thema, id=graphene.Int())

    def resolve_thema(root, info, **kwargs):
        id = kwargs.get('id')

        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas where id=:id',
                        id=id)
        return results.first(default=GraphQLError(f'Thema met id {id} is niet gevonden'))

    def resolve_all_themas(root, info):
        db = records.Database("sqlite:///mock.db")
        results = db.query('select * from themas')
        return results
        # return [{'naam':'Swen', 'beschrijving':'Ik ben een Swen'}]


Schema = Schema(query=Query)
