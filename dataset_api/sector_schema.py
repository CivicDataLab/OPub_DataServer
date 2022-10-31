import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from django.db.models import Q

from .models import Sector, Dataset, Catalog


class SectorType(DjangoObjectType):
    class Meta:
        model = Sector
        fields = "__all__"


class SectorStatsType(graphene.ObjectType):
    dataset_count = graphene.Int()
    api_count = graphene.Int()
    organization_count = graphene.Int()


class Query(graphene.ObjectType):
    all_sector = graphene.List(SectorType)
    sector = graphene.Field(SectorType, sector_id=graphene.Int())
    sector_stat = graphene.Field(SectorStatsType, sector_id=graphene.Int())

    def resolve_all_sector(self, info, **kwargs):
        return Sector.objects.all()

    def resolve_sector(self, info, sector_id):
        return Sector.objects.get(pk=sector_id)

    def resolve_sector_stat(self, info, sector_id):
        dataset = Sector.objects.get(pk=sector_id).dataset_set.count()
        api_count = Dataset.objects.filter(
            Q(dataset_type__exact="API"), Q(sector__pk=sector_id)
        ).count()
        dataset_obj = Dataset.objects.filter(sector__pk=sector_id)
        org_list = []
        for catalog in dataset_obj:
            org_list.append(Catalog.objects.get(id=catalog.catalog_id).organization.id)
        org_count = len(set(org_list))
        return SectorStatsType(
            dataset_count=dataset, api_count=api_count, organization_count=org_count
        )


class SectorInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String()
    highlights = graphene.List(of_type=graphene.String)
    # organization = graphene.String()


class CreateSector(Output, graphene.Mutation):
    class Arguments:
        sector_data = SectorInput(required=True)

    sector = graphene.Field(SectorType)

    @staticmethod
    def mutate(root, info, sector_data=None):
        sector_instance = Sector(
            name=sector_data.name,
            description=sector_data.description,
            highlights=sector_data.highlights,
        )
        sector_instance.save()
        return CreateSector(sector=sector_instance)


class Mutation(graphene.ObjectType):
    create_sector = CreateSector.Field()
