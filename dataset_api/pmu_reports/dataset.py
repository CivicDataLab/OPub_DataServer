import graphene
from graphql import GraphQLError
from django.db.models import Count, Q
from graphene_django import DjangoObjectType

from dataset_api.dataset.schema import DatasetType
from dataset_api.models import Sector, Geography, Dataset, Organization
from dataset_api.decorators import auth_user_by_org
from dataset_api.utils import add_pagination_filters


class SectorItem(graphene.ObjectType):
    sector_name = graphene.String()
    sector_id = graphene.String()


class GeographyItem(graphene.ObjectType):
    geograph_name = graphene.String()
    geography_id = graphene.String()


class OrgsItem(graphene.ObjectType):
    org_title = graphene.String()
    org_id = graphene.String()


class Filters(graphene.ObjectType):
    sectors = graphene.List(SectorItem)
    geographies = graphene.List(GeographyItem)
    providers = graphene.List(OrgsItem)


class DatasetCount(graphene.ObjectType):
    title = graphene.String()
    id = graphene.String()
    dataset_count = graphene.String()


class Query(graphene.ObjectType):
    all_dataset_filters = graphene.Field(Filters)
    dataset_count_org = graphene.Field(
        graphene.List(DatasetCount),
        by=graphene.String(),
        sector=graphene.String(),
        geo=graphene.String(),
        org=graphene.String(),
        frm=graphene.String(),
        to=graphene.String(),
    )
    dataset_by_downloads = graphene.Field(
        graphene.List(DatasetType),
        sector=graphene.String(),
        geo=graphene.String(),
        org=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
        frm=graphene.String(),
        to=graphene.String(),
        hvd=graphene.Boolean(),
    )

    @auth_user_by_org(action="query")
    def resolve_all_dataset_filters(self, info, role):
        if role == "PMU":
            sector_list = []
            provider_list = []
            geography_list = []

            for sector in (
                Sector.objects.filter(dataset__status="PUBLISHED")
                .order_by("name")
                .distinct()
            ):
                sector_list.append(SectorItem(sector.name, sector.id))

            for geo in (
                Geography.objects.filter(dataset__status="PUBLISHED")
                .order_by("name")
                .distinct()
            ):
                geography_list.append(GeographyItem(geo.name, geo.id))

            for organization in (
                Organization.objects.filter(catalog__dataset__status="PUBLISHED")
                .order_by("title")
                .distinct()
            ):
                provider_list.append(OrgsItem(organization.title, organization.id))

            return Filters(sector_list, geography_list, provider_list)
        else:
            raise GraphQLError("Access Denied")

    # def resolve_datasets_with_sector(self, info, role, sector_id):
    #     if role == "DPA" or role == "PMU" or role == "DP":
    #         return Dataset.objects.filter(sector__id=sector_id).order_by("title")
    #     else:
    #         raise GraphQLError("Access Denied")

    # def resolve_datasets_with_geography(self, info, role, geography_id):
    #     if role == "DPA" or role == "PMU" or role == "DP":
    #         return Dataset.objects.filter(geography__id=geography_id).order_by("title")
    #     else:
    #         raise GraphQLError("Access Denied")

    # def resolve_datasets_with_provider(self, info, role, org_id):
    #     if role == "DPA" or role == "PMU" or role == "DP":
    #         return Dataset.objects.filter(catalog__organization__id=org_id).order_by("title")
    #     else:
    #         raise GraphQLError("Access Denied")

    @auth_user_by_org(action="query")
    def resolve_dataset_count_org(
        self,
        info,
        by,
        role,
        sector=None,
        geo=None,
        org=None,
        frm=None,
        to=None,
    ):
        if sector:
            # if by == "Organization":
            #     sector_query = {
            #         "{0}__{1}__{2}".format("catalog", "dataset", "sector"): sector
            #     }
            # else:
            sector_query = {"{0}".format("sector"): sector}
        if geo:
            # if by == "Organization":
            #     geo_query = {
            #         "{0}__{1}__{2}".format("catalog", "dataset", "geography"): geo
            #     }
            # else:
            geo_query = {"{0}".format("geography"): geo}
        if org:
            if by == "Sector" or by == "Geography":
                org_query = {"{0}__{1}".format("catalog", "organization"): org}
        if frm:
            frm_query = {"{0}__{1}__{2}".format("published_date", "date", "gte"): frm}
        if to:
            to_query = {"{0}__{1}__{2}".format("published_date", "date", "lte"): to}

        if role == "PMU":
            dataset_org = []

            if by == "Entity":
                # org_obj = Organization.objects.filter(
                #     catalog__dataset__status="PUBLISHED"
                # ).order_by("title")
                dataset_obj = Dataset.objects.filter(status="PUBLISHED")
                if org:  # For Organization based filtering, along with others.
                    dataset_obj = dataset_obj.filter(catalog__organization__id=org)
                if sector:
                    dataset_obj = dataset_obj.filter(**sector_query)
                if geo:
                    dataset_obj = dataset_obj.filter(**geo_query)
                if frm:
                    dataset_obj = dataset_obj.filter(**frm_query)
                if to:
                    dataset_obj = dataset_obj.filter(**to_query)

                dataset_obj = (
                    dataset_obj.values(
                        "catalog__organization__title", "catalog__organization__id"
                    )
                    .annotate(dt_count=Count("catalog__organization__title"))
                    .order_by("-dt_count")
                )
                for org in dataset_obj:
                    dataset_org.append(
                        DatasetCount(
                            org["catalog__organization__title"],
                            org["catalog__organization__id"],
                            org["dt_count"],
                        )
                    )
                return dataset_org

            elif by == "Sector":
                if not any([sector, geo, org]):
                    sector_obj = Sector.objects.all()
                    for sectors in sector_obj:
                        dataset_obj = Dataset.objects.filter(
                            status="PUBLISHED", sector=sectors.pk
                        )
                        if dataset_obj:
                            dataset_org.append(
                                DatasetCount(
                                    sectors.name, sectors.pk, dataset_obj.count()
                                )
                            )
                    return dataset_org
                else:
                    if sector:
                        sector_obj = Sector.objects.get(pk=sector)
                        dataset_obj = Dataset.objects.filter(
                            status="PUBLISHED", sector=sector
                        )
                        if org:
                            dataset_obj = dataset_obj.filter(**org_query)
                        if geo:
                            dataset_obj = dataset_obj.filter(**geo_query)
                        if frm:
                            dataset_obj = dataset_obj.filter(**frm_query)
                        if to:
                            dataset_obj = dataset_obj.filter(**to_query)
                        if dataset_obj:
                            dataset_org.append(
                                DatasetCount(
                                    sector_obj.name, sector_obj.id, dataset_obj.count()
                                )
                            )
                    else:
                        sector_obj = Sector.objects.all()
                        for sectors in sector_obj:
                            dataset_obj = Dataset.objects.filter(
                                status="PUBLISHED", sector=sectors.pk
                            )
                            if org:
                                dataset_obj = dataset_obj.filter(**org_query)
                            if geo:
                                dataset_obj = dataset_obj.filter(**geo_query)
                            if frm:
                                dataset_obj = dataset_obj.filter(**frm_query)
                            if to:
                                dataset_obj = dataset_obj.filter(**to_query)
                            if dataset_obj:
                                dataset_org.append(
                                    DatasetCount(
                                        sectors.name, sectors.pk, dataset_obj.count()
                                    )
                                )
                    return dataset_org

            elif by == "Geography":
                if geo:
                    geo_obj = Geography.objects.get(pk=geo)
                    dataset_obj = Dataset.objects.filter(
                        status="PUBLISHED", geography=geo
                    )
                    if org:
                        dataset_obj = dataset_obj.filter(**org_query)
                    if sector:
                        dataset_obj = dataset_obj.filter(**sector_query)
                    if frm:
                        dataset_obj = dataset_obj.filter(**frm_query)
                    if to:
                        dataset_obj = dataset_obj.filter(**to_query)
                    if dataset_obj:
                        dataset_org.append(
                            DatasetCount(geo_obj.name, geo_obj.id, dataset_obj.count())
                        )
                else:
                    geo_obj = Geography.objects.all()
                    for geos in geo_obj:
                        dataset_obj = Dataset.objects.filter(
                            status="PUBLISHED",
                            geography=geos.pk,
                        )
                        if org:
                            dataset_obj = dataset_obj.filter(**org_query)
                        if geo:
                            dataset_obj = dataset_obj.filter(**geo_query)
                        if frm:
                            dataset_obj = dataset_obj.filter(**frm_query)
                        if to:
                            dataset_obj = dataset_obj.filter(**to_query)
                        if dataset_obj:
                            dataset_org.append(
                                DatasetCount(geos.name, geos.pk, dataset_obj.count())
                            )
                return dataset_org
        else:
            raise GraphQLError("Access Denied")

    @auth_user_by_org(action="query")
    def resolve_dataset_by_downloads(
        self,
        info,
        role,
        sector=None,
        geo=None,
        org=None,
        first=None,
        skip=None,
        frm=None,
        to=None,
        hvd=False,
    ):
        if role == "PMU":
            dataset_obj = Dataset.objects.filter(status="PUBLISHED")
            if sector:
                dataset_obj = dataset_obj.filter(sector=sector)
            if geo:
                dataset_obj = dataset_obj.filter(geography=geo)
            if org:
                dataset_obj = dataset_obj.filter(catalog__organization=org)
            if frm:
                dataset_obj = dataset_obj.filter(published_date__date__gte=frm)
            if to:
                dataset_obj = dataset_obj.filter(published_date__date__lte=to)
            if hvd:
                dataset_obj = dataset_obj.filter(hvd_rating__gte=4)
            # if not any([sector, geo, org, frm, to]):
            #     dataset_obj = Dataset.objects.filter(status="PUBLISHED")

            dataset_obj = add_pagination_filters(
                first, dataset_obj.order_by("-download_count"), skip
            )
            return dataset_obj
        else:
            raise GraphQLError("Access Denied")
