import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from .models import Organization, Geography


class GeographyType(DjangoObjectType):
    class Meta:
        model = Geography
        fields = "__all__"


class Query(graphene.ObjectType):
    all_geography = graphene.List(GeographyType)
    geography = graphene.Field(GeographyType, geography_id=graphene.Int())

    def resolve_all_geography(self, info, **kwargs):
        return Geography.objects.all()

    def resolve_geography(self, info, geography_id):
        return Geography.objects.get(pk=geography_id)


class GeographyInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    official_id = graphene.String()
    # organization = graphene.String()


class CreateGeography(Output, graphene.Mutation):
    class Arguments:
        geography_data = GeographyInput(required=True)

    geography = graphene.Field(GeographyType)

    @staticmethod
    def mutate(root, info, geography_data=None):
        # organization = Organization.objects.get(id=geography_data.organization)
        geography_instance = Geography(
            name=geography_data.name,
            official_id=geography_data.official_id,
        )
        geography_instance.save()
        return CreateGeography(geography=geography_instance)
    
class UpdateGeography(Output, graphene.Mutation):
    class Arguments:
        geography_data = GeographyInput(required=True)

    sector = graphene.Field(GeographyType)

    @staticmethod
    def mutate(root, info, geography_data=None):
        geography_instance = Geography.objects.get(id=geography_data.official_id)
        geography_instance.name = geography_data.name          
        geography_instance.save()
        return UpdateGeography(sector=geography_instance)    


class Mutation(graphene.ObjectType):
    create_geography = CreateGeography.Field()
    update_geography = UpdateGeography.Field()
