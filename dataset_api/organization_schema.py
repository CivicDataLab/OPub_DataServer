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

    def resolve_all_organizations(self, info, **kwargs):
        return Organization.objects.all()

    def resolve_organizaiton(self, info, organizaiton_id):
        return Organization.objects.get(pk=organizaiton_id)


class OrganizationInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String()
    description = graphene.String()


class CreateOrganization(graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(OrganizationType)

    @staticmethod
    def mutate(root, info, organization_data=None):
        organization_instance = Organization(
            title=organization_data.title,
            description=organization_data.description,
        )
        organization_instance.save()
        return CreateOrganization(organization=organization_instance)
