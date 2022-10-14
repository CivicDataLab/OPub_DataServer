import graphene
from graphene_django import DjangoObjectType

from .models import Sector, Geography, Organization, Dataset


class Query(graphene.ObjectType):
    sector_count = graphene.String()
    geography_count = graphene.String()   
    organization_count = graphene.String()
    dataset_count = graphene.String()

    def resolve_sector_count(self, info, **kwargs):
        return Sector.objects.count()
    
    def resolve_geography_count(self, info, **kwargs):
        return Geography.objects.count()
    
    def resolve_organization_count(self, info, **kwargs):
        return Organization.objects.count()
    
    def resolve_dataset_count(self, info, **kwargs):
        return Dataset.objects.count()