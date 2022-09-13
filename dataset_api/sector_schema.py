import graphene
from graphene_django import DjangoObjectType

from .models import Sector


class SectorType(DjangoObjectType):
    class Meta:
        model = Sector
        fields = "__all__"


class Query(graphene.ObjectType):
    all_sector = graphene.List(SectorType)
    sector = graphene.Field(SectorType, sector_id=graphene.Int())

    def resolve_all_sector(self, info, **kwargs):
        return Sector.objects.all()

    def resolve_sector(self, info, sector_id):
        return Sector.objects.get(pk=sector_id)


class SectorInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    # organization = graphene.String()


class CreateSector(graphene.Mutation):
    class Arguments:
        sector_data = SectorInput(required=True)

    sector = graphene.Field(SectorType)

    @staticmethod
    def mutate(root, info, sector_data=None):
        sector_instance = Sector(
            name=sector_data.name,
        )
        sector_instance.save()
        return CreateSector(sector=sector_instance)


class Mutation(graphene.ObjectType):
    create_sector = CreateSector.Field()
