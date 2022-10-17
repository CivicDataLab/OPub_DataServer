import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import Organization
from .decorators import validate_token, create_user_org

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
    logo = Upload(required=False, description="Logo for the Company.")
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)


class CreateOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(OrganizationType)

    @staticmethod
    @create_user_org
    def mutate(root, info, organization_data: OrganizationInput = None):
        organization_instance = Organization(
            title=organization_data.title,
            description=organization_data.description,
            logo=organization_data.logo,
            contact_email=organization_data.contact,
            homepage=organization_data.homepage
        )
        organization_instance.save()
        return CreateOrganization(organization=organization_instance)


class UpdateOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(OrganizationType)

    @staticmethod
    @validate_token
    def mutate(root, info, organization_data: OrganizationInput = None):
        organization_instance = Organization.objects.get(id=organization_data.id)
        if organization_instance:
            organization_instance.title = organization_data.title
            organization_instance.description = organization_data.description
            organization_instance.logo = organization_data.logo
            organization_instance.contact_email = organization_data.contact
            organization_instance.homepage = organization_data.homepage
            organization_instance.save()
        return CreateOrganization(organization=organization_instance)


class Mutation(graphene.ObjectType):
    create_organization = CreateOrganization.Field()
    update_organization = UpdateOrganization.Field()
