import graphene
from django.db.models import Q

from .enums import OrganizationCreationStatusType
from .models import Sector, Geography, Organization, Dataset, Resource


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
        geography = Dataset.objects.filter(status="PUBLISHED").values_list("geography", flat=True).distinct().count()
        organization = Organization.objects.filter(
            organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value).count()
        dataset = Dataset.objects.filter(status="PUBLISHED").count()
        api = Resource.objects.filter(Q(dataset__status__exact="PUBLISHED")).count()

        return StatsType(
            sector_count=sector,
            geography_count=geography,
            organization_count=organization,
            dataset_count=dataset,
            api_count=api,
        )
