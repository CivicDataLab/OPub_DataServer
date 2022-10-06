import graphene
from graphene_django import DjangoObjectType

from .models import Catalog, Organization


class CatalogType(DjangoObjectType):
    class Meta:
        model = Catalog
        fields = "__all__"


class Query(graphene.ObjectType):
    all_catalog = graphene.List(CatalogType)
    catalog = graphene.Field(CatalogType, catalog_id=graphene.Int())

    def resolve_all_catalog(self, info, **kwargs):
        return Catalog.objects.all().order_by("-modified")

    def resolve_catalog(self, info, catalog_id):
        return Catalog.objects.get(pk=catalog_id)


class CatalogInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String()
    description = graphene.String()
    organization = graphene.String()


class CreateCatalog(graphene.Mutation):
    class Arguments:
        catalog_data = CatalogInput(required=True)

    catalog = graphene.Field(CatalogType)

    @staticmethod
    def mutate(root, info, catalog_data=None):
        organization = Organization.objects.get(id=catalog_data.organization)
        catalog_instance = Catalog(
            title=catalog_data.title,
            description=catalog_data.description,
            organization=organization
        )
        catalog_instance.save()
        return CreateCatalog(catalog=catalog_instance)
