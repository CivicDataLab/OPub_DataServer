import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

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
    title = graphene.String(required=True)
    description = graphene.String(required=True)


class CreateCatalog(Output, graphene.Mutation):
    class Arguments:
        catalog_data = CatalogInput(required=True)

    catalog = graphene.Field(CatalogType)

    @staticmethod
    def mutate(root, info, catalog_data=None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Organization with given id not found", "code": "404"}]}}
        catalog_instance = Catalog(
            title=catalog_data.title,
            description=catalog_data.description,
            organization=organization
        )
        catalog_instance.save()
        return CreateCatalog(catalog=catalog_instance)


class Mutation(graphene.ObjectType):
    create_catalog = CreateCatalog.Field()
