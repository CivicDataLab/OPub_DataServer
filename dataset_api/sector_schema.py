import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from django.db.models import Q, Sum

from .models import Sector, Dataset, Catalog, DatasetAccessModel


class SectorType(DjangoObjectType):
    dataset_count = graphene.Int()
    api_count = graphene.Int()
    organization_count = graphene.Int()
    downloads = graphene.Int()
    dam_count = graphene.Int()

    class Meta:
        model = Sector
        fields = "__all__"

    def resolve_dataset_count(self, info):
        try:
            dataset_count = Dataset.objects.filter(
                Q(status__exact="PUBLISHED"), Q(sector__pk=self.id)
            ).count()
            return dataset_count
        except Sector.DoesNotExist as e:
            return None

    def resolve_api_count(self, info):
        api_count = Dataset.objects.filter(
            Q(dataset_type__exact="API"), Q(sector__pk=self.id)
        ).count()
        return api_count

    def resolve_organization_count(self, info):
        dataset_obj = Dataset.objects.filter(sector__pk=self.id)
        org_list = []
        for catalog in dataset_obj:
            org_list.append(Catalog.objects.get(id=catalog.catalog_id).organization.id)
        return len(set(org_list))

    def resolve_downloads(self, info):
        return Dataset.objects.filter(sector__pk=self.id).aggregate(
            Sum("download_count")
        )

    def resolve_dam_count(self, info):
        dataset_obj = Dataset.objects.filter(sector__pk=self.id)
        dam_count = DatasetAccessModel.objects.filter(dataset_id__in=dataset_obj, dataset__status__exact="PUBLISHED").count()
        return dam_count


class Query(graphene.ObjectType):
    all_sector = graphene.List(SectorType)
    active_sector = graphene.List(SectorType)
    sector = graphene.Field(SectorType, sector_id=graphene.Int())
    sector_by_title = graphene.Field(SectorType, sector_title=graphene.String())

    def resolve_all_sector(self, info, **kwargs):
        return Sector.objects.all().order_by("name").distinct()

    def resolve_active_sector(self, info, **kwargs):
        return Sector.objects.filter(dataset__status="PUBLISHED").order_by("name").distinct()

    def resolve_sector(self, info, sector_id):
        return Sector.objects.get(pk=sector_id)

    def resolve_sector_by_title(self, info, sector_title):
        return Sector.objects.get(name__iexact=sector_title)


class SectorInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String()
    highlights = graphene.List(of_type=graphene.String)
    official_id = graphene.String(required=False)
    # organization = graphene.String()
    parent_id = graphene.String(required=False)


class CreateSector(Output, graphene.Mutation):
    class Arguments:
        sector_data = SectorInput(required=True)

    sector = graphene.Field(SectorType)

    @staticmethod
    def mutate(root, info, sector_data=None):
        parent_instance = None
        if sector_data.parent_id:
            parent_instance = Sector.objects.get(pk=sector_data.parent_id)
        sector_instance = Sector(
            name=sector_data.name,
            description=sector_data.description,
            highlights=sector_data.highlights,
            official_id=sector_data.official_id,
            parent_id=parent_instance,
        )
        sector_instance.save()
        return CreateSector(sector=sector_instance)


class UpdateSector(Output, graphene.Mutation):
    class Arguments:
        sector_data = SectorInput(required=True)

    sector = graphene.Field(SectorType)

    @staticmethod
    def mutate(root, info, sector_data=None):
        sector_instance = Sector.objects.get(official_id=sector_data.official_id)
        sector_instance.name = sector_data.name
        if sector_data.description:
            sector_instance.description = sector_data.description
        if sector_data.highlights:
            sector_instance.highlights = sector_data.highlights
        if sector_data.official_id:
            sector_instance.official_id = sector_data.official_id
        if sector_data.parent_id:
            parent_instance = Sector.objects.get(pk=sector_data.parent_id)
            sector_instance.parent_id = parent_instance
        sector_instance.save()
        return UpdateSector(sector=sector_instance)


class Mutation(graphene.ObjectType):
    create_sector = CreateSector.Field()
    update_sector = UpdateSector.Field()
