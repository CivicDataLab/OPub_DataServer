import graphene
from graphene_django import DjangoObjectType

from .models import Organization


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Organization
        fields = "__all__"


class Query(graphene.ObjectType):
    all_organizations = graphene.List(OrganizationType)
    organization = graphene.Field(OrganizationType, organization_id=graphene.Int())
    organization_by_title = graphene.Field(OrganizationType, organization_title=graphene.String())

    def resolve_all_organizations(self, info, **kwargs):
        return Organization.objects.all().order_by("-modified")

    def resolve_organization(self, info, organization_id):
        return Organization.objects.get(pk=organization_id)

    def resolve_organization_by_title(self, info, organization_title):
        return Organization.objects.get(title__iexact=organization_title)


class OrganizationInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)


class CreateOrganization(graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(OrganizationType)

    @staticmethod
    def mutate(root, info, organization_data: OrganizationInput = None):
        organization_instance = Organization(
            title=organization_data.title,
            description=organization_data.description,
            contact_email=organization_data.contact,
            homepage=organization_data.homepage
        )
        organization_instance.save()
        return CreateOrganization(organization=organization_instance)
