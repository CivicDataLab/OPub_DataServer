import graphene
from django.db.models import Q

from .models import Sector, Geography, Organization, Dataset


class StatsType(graphene.ObjectType):
    sector_count = graphene.Int()
    geography_count = graphene.Int()
    organization_count = graphene.Int()
    dataset_count = graphene.Int()
    api_count = graphene.Int()


class Query(graphene.ObjectType):
    stat_count = graphene.Field(StatsType)

    def resolve_stat_count(self, info, **kwargs):
        sector = Sector.objects.count()
        geography = Geography.objects.count()
        organization = Organization.objects.count()
        dataset = Dataset.objects.count()
        api = Dataset.objects.filter(
            Q(dataset_type__exact="API"), Q(status__exact="PUBLISHED")
        ).count()

        return StatsType(
            sector_count=sector,
            geography_count=geography,
            organization_count=organization,
            dataset_count=dataset,
            api_count=api,
        )
