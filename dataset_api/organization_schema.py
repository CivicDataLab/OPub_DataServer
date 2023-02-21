import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_auth.bases import Output

from activity_log.signal import activity
from .constants import IMAGE_FORMAT_MAPPING
from .decorators import (
    validate_token,
    validate_token_or_none,
    create_user_org,
    auth_user_by_org,
    auth_request_org,
    modify_org_status,
    get_user_org,
    get_child_orgs_dpa,
)
from .enums import (
    OrganizationTypes,
    OrganizationCreationStatusType,
    RatingStatus,
    OrganizationSubTypes,
)
from .file_utils import file_validation
from .models import (
    Organization,
    OrganizationCreateRequest,
    Catalog,
    Resource,
    Dataset,
    Sector,
    DatasetAccessModelRequest,
    DatasetAccessModel,
    DataAccessModel,
    Geography,
)

from .utils import get_client_ip, get_average_rating, log_activity


class CreateOrganizationType(DjangoObjectType):
    class Meta:
        model = OrganizationCreateRequest
        fields = "__all__"


class OrganizationType(DjangoObjectType):
    username = graphene.String()
    api_count = graphene.Int()
    dataset_count = graphene.Int()
    usecase_count = graphene.Int()
    user_count = graphene.Int()
    average_rating = graphene.Float()
    dam_count = graphene.Int()

    class Meta:
        model = Organization
        fields = "__all__"

    @auth_request_org
    def resolve_username(self, info, username=""):
        return username

    def resolve_average_rating(self, info):
        pub_datasets = Dataset.objects.filter(
            Q(status__exact="PUBLISHED"),
            Q(catalog__organization=self.id),
        )
        count = 0
        rating = 0
        for dataset in pub_datasets:
            dataset_rating = get_average_rating(dataset)
            if dataset_rating > 0:
                count = count + 1
                rating = rating + dataset_rating
        return rating / count if rating else 0

    def resolve_api_count(self, info):
        api = Resource.objects.filter(
            Q(dataset__dataset_type__exact="API"),
            Q(dataset__status__exact="PUBLISHED"),
            Q(dataset__catalog__organization=self.id),
        ).count()
        return api

    def resolve_dataset_count(self, info):
        dataset = Dataset.objects.filter(
            Q(status__exact="PUBLISHED"),
            Q(catalog__organization=self.id),
        ).count()
        return dataset

    def resolve_usecase_count(self, info):
        usecase = Sector.objects.filter(
            Q(dataset__catalog__organization=self.id),
            Q(dataset__status__exact="PUBLISHED"),
        )
        return len(set(usecase))

    def resolve_user_count(self, info):
        user_count = (
            DatasetAccessModelRequest.objects.filter(
                Q(access_model_id__dataset_id__catalog__organization=self.id),
                Q(access_model_id__dataset__status__exact="PUBLISHED"),
            )
            .values_list("user")
            .distinct()
            .count()
        )
        return user_count

    def resolve_dam_count(self, info):
        org_datasets = Dataset.objects.filter(
            catalog__organization=self.id, status="PUBLISHED"
        )
        dam_count = DatasetAccessModel.objects.filter(dataset__in=org_datasets).count()
        return dam_count


class Query(graphene.ObjectType):
    all_organizations = graphene.List(OrganizationType)
    organization_by_id = graphene.Field(
        OrganizationType, organization_id=graphene.Int()
    )
    organization_by_title = graphene.Field(
        OrganizationType, organization_title=graphene.String()
    )
    organizations = graphene.List(OrganizationType)

    requested_rejected_organizations = graphene.List(OrganizationType)
    organizations_by_user = graphene.List(OrganizationType)
    organization_without_dpa = graphene.List(
        OrganizationType, organization_id=graphene.Int()
    )
    ministries_by_state = graphene.List(OrganizationType, state=graphene.String())
    dept_by_ministry = graphene.List(
        OrganizationType, state=graphene.String(), organization_id=graphene.Int()
    )

    # TODO: Allow all org list for PMU? Current State -- YES
    @auth_user_by_org(action="query")
    def resolve_all_organizations(self, info, role, **kwargs):
        if role == "PMU":
            return Organization.objects.all().order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    # Access : DPA of that org.
    @auth_user_by_org(action="query")
    def resolve_organization_by_id(self, info, role, organization_id):
        if role == "DPA" or role == "PMU" or role == "DP":
            return Organization.objects.get(pk=organization_id)
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU or DPA of that org.
    @auth_user_by_org(action="query")
    @get_child_orgs_dpa
    def resolve_organization_without_dpa(self, info, role, organization_id, **kwargs):
        if role == "DPA" or role == "PMU":
            return Organization.objects.filter(pk__in=kwargs["org_without_dpa"])
        else:
            raise GraphQLError("Access Denied")

    # Access : All
    def resolve_organization_by_title(self, info, organization_title, **kwargs):
        return Organization.objects.get(
            Q(title__iexact=organization_title),
            Q(
                organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
            ),
        )

    # Access : All
    def resolve_organizations(self, info, **kwargs):
        return Organization.objects.filter(
            organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
        ).order_by("-modified")

    # Access : PMU
    @auth_user_by_org(action="query")
    def resolve_requested_rejected_organizations(self, info, role, **kwargs):
        if role == "PMU":
            return Organization.objects.filter(
                ~Q(
                    organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
                )
            ).order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    @get_user_org
    def resolve_organizations_by_user(self, info, org_ids, **kwargs):
        return Organization.objects.filter(
            organizationcreaterequest__organization_ptr_id__in=org_ids
        ).order_by("-modified")

    def resolve_ministries_by_state(self, info, state):
        state_obj = Geography.objects.get(name=state)
        return Organization.objects.filter(
            organizationcreaterequest__organization_subtypes="MINISTRY",
            organizationcreaterequest__state=state_obj,
        )

    def resolve_dept_by_ministry(self, info, state, organization_id):
        state_obj = Geography.objects.get(name=state)
        return Organization.objects.filter(
            parent_id=organization_id,
            organizationcreaterequest__state=state_obj,
        )


class OrganizationInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    logo = Upload(required=False, description="Logo for the Company.")
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)
    organization_types = graphene.Enum.from_enum(OrganizationTypes)(required=True)
    data_description = graphene.String(required=False)
    upload_sample_data_file = Upload(required=False)
    sample_data_url = graphene.String(required=False)
    dpa_email = graphene.String(required=False)
    parent_id = graphene.ID(required=False)
    address = graphene.String(required=False)
    state = graphene.String(required=False)
    gov_sub_type = graphene.Enum.from_enum(OrganizationSubTypes)(required=True)


class OrganizationPatchInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=False)
    description = graphene.String(required=False)
    logo = Upload(required=False, description="Logo for the Company.")
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)
    address = graphene.String(required=False)


class ApproveRejectOrganizationApprovalInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = graphene.Enum.from_enum(OrganizationCreationStatusType)(required=True)
    remark = graphene.String(required=False)


class CreateOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(CreateOrganizationType)

    @staticmethod
    @validate_token
    @create_user_org
    def mutate(
        root, info, username, organization_data: OrganizationInput = None
    ):
        # try:
        #     OrganizationCreateRequest.objects.get(
        #         Q(organization_ptr_id__title__iexact=organization_data.title),
        #         Q(status="APPROVED"),
        #     )
        #     raise GraphQLError("Organization with given name already exists.")
        # except Organization.DoesNotExist:
        # try:
        #     OrganizationCreateRequest.objects.get(
        #         Q(organization_ptr_id__title__iexact=organization_data.title),
        #         Q(username=username),
        #     )
        #     raise GraphQLError("You have already requested for this Organization.")
        # except Organization.DoesNotExist:
        geography_obj = None
        if organization_data.state:
            try:
                geography_obj = Geography.objects.get(name=organization_data.state)
            except Geography.DoesNotExist:
                raise GraphQLError("Given location doesn't exists!")

        organization_additional_info_instance = OrganizationCreateRequest(
            title=organization_data.title,
            description=organization_data.description,
            logo=organization_data.logo,
            contact_email=organization_data.contact,
            homepage=organization_data.homepage,
            organization_types=organization_data.organization_types,
            upload_sample_data_file=organization_data.upload_sample_data_file,
            data_description=organization_data.data_description,
            sample_data_url=organization_data.sample_data_url,
            status=OrganizationCreationStatusType.APPROVED.value,
            username=username,
            dpa_email=organization_data.dpa_email,
            parent_id=organization_data.parent_id,
            address=organization_data.address,
            state=geography_obj,
            organization_subtypes=organization_data.gov_sub_type,
        )
        organization_additional_info_instance.save()

        # Create catalog.
        catalog_instance = Catalog(
            title=organization_additional_info_instance.title,
            description=organization_additional_info_instance.description,
            organization=organization_additional_info_instance,
        )
        catalog_instance.save()

        if organization_data.logo:
            mime_type = file_validation(
                organization_additional_info_instance.logo,
                organization_additional_info_instance.logo,
                IMAGE_FORMAT_MAPPING,
            )
            if not mime_type:
                organization_additional_info_instance.delete()
                raise GraphQLError("Unsupported Logo Format")
            else:
                logo_format = IMAGE_FORMAT_MAPPING.get(mime_type.lower())
                if not logo_format:
                    organization_additional_info_instance.delete()
                    raise GraphQLError("Unsupported Logo Format")
        # mime_type = magic.from_file(organization_additional_info_instance.logo.path, mime=True)
        # mime_type = mimetypes.guess_type(
        #     organization_additional_info_instance.logo.path
        # )

        log_activity(
            target_obj=organization_additional_info_instance,
            ip=get_client_ip(info),
            username=username,
            target_group=organization_additional_info_instance,
            verb=OrganizationCreationStatusType.APPROVED.value,
        )
        return CreateOrganization(organization=organization_additional_info_instance)


class UpdateOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(CreateOrganizationType)

    @staticmethod
    @validate_token_or_none
    @auth_user_by_org(action="update_organization")
    def mutate(root, info, role, username, organization_data: OrganizationInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        org_id = organization_data.id if organization_data.id else org_id
        try:
            organization_create_request_instance = (
                OrganizationCreateRequest.objects.get(organization_ptr_id=org_id)
            )
        except OrganizationCreateRequest.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Organization with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        organization_create_request_instance.title = organization_data.title
        organization_create_request_instance.description = organization_data.description
        organization_create_request_instance.logo = organization_data.logo
        organization_create_request_instance.contact_email = organization_data.contact
        organization_create_request_instance.homepage = organization_data.homepage
        organization_create_request_instance.address = organization_data.address
        organization_create_request_instance.organization_types = (
            organization_data.organization_types
        )
        organization_create_request_instance.data_description = (
            organization_data.data_description
        )
        organization_create_request_instance.sample_data_url = (
            organization_data.sample_data_url
        )
        organization_create_request_instance.upload_sample_data_file = (
            organization_data.upload_sample_data_file
        )
        organization_create_request_instance.save()

        log_activity(
            target_obj=organization_create_request_instance,
            ip=get_client_ip(info),
            username=username,
            target_group=organization_create_request_instance,
            verb="Updated",
        )

        return UpdateOrganization(organization=organization_create_request_instance)


class ApproveRejectOrganizationApproval(Output, graphene.Mutation):
    class Arguments:
        organization_data = ApproveRejectOrganizationApprovalInput(required=True)

    organization = graphene.Field(CreateOrganizationType)
    rejected = graphene.List(graphene.String)  # For Auth via decorator.

    @staticmethod
    @validate_token
    @auth_user_by_org(action="approve_organization")
    @modify_org_status
    def mutate(
        root,
        info,
        username,
        organization_data: ApproveRejectOrganizationApprovalInput = None,
    ):
        try:
            organization_create_request_instance = (
                OrganizationCreateRequest.objects.get(
                    organization_ptr_id=organization_data.id
                )
            )
        except OrganizationCreateRequest.DoesNotExist as e:
            raise GraphQLError("Organization with given id not found")
        try:
            organization = Organization.objects.get(pk=organization_data.id)
            OrganizationCreateRequest.objects.get(
                Q(organization_ptr_id__title=organization.title),
                Q(status="APPROVED"),
            )
            raise GraphQLError("Organization with given name already exists.")
        except Organization.DoesNotExist:
            if organization_data.status == "REJECTED":
                organization_create_request_instance.status = (
                    OrganizationCreationStatusType.REJECTED.value
                )
                organization_create_request_instance.remark = organization_data.remark
                organization_create_request_instance.save()

                activity.send(
                    username,
                    verb=organization_data.status,
                    target=organization_create_request_instance,
                    target_group=organization_create_request_instance,
                    ip=get_client_ip(info),
                )

                return ApproveRejectOrganizationApproval(
                    organization=organization_create_request_instance,
                    rejected=None,
                )
            else:
                organization_create_request_instance.status = (
                    OrganizationCreationStatusType.APPROVED.value
                )

                # Create catalog if org is APPROVED.
                catalog_instance = Catalog(
                    title=organization.title,
                    description=organization.description,
                    organization=organization,
                )
                catalog_instance.save()

            organization_create_request_instance.remark = organization_data.remark
            organization_create_request_instance.save()

            same_org_instance = OrganizationCreateRequest.objects.filter(
                organization_ptr_id__title__iexact=organization.title
            )
            if same_org_instance.exists():
                rejected_list = []
                for orgs in same_org_instance:
                    if not orgs.status == "APPROVED":
                        orgs.status = OrganizationCreationStatusType.REJECTED.value
                        orgs.remark = "Organization with given name already exists."
                        orgs.save()
                        rejected_list.append(orgs.organization_ptr_id)

                        # Activity log for REJECTED organization.
                        activity.send(
                            username,
                            verb=orgs.status,
                            target=orgs,
                            target_group=orgs,
                            ip=get_client_ip(info),
                        )

            # Activity log for APPROVED organization.
            activity.send(
                username,
                verb=organization_data.status,
                target=organization_create_request_instance,
                target_group=organization_create_request_instance,
                ip=get_client_ip(info),
            )
            return ApproveRejectOrganizationApproval(
                organization=organization_create_request_instance,
                rejected=rejected_list,
            )


class PatchOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationPatchInput(required=True)

    organization = graphene.Field(OrganizationType)

    @staticmethod
    @auth_user_by_org(action="update_organization")
    def mutate(root, info, organization_data: OrganizationPatchInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        org_id = organization_data.id if organization_data.id else org_id
        organization_instance = Organization.objects.get(id=org_id)

        if organization_data.title:
            organization_instance.title = organization_data.title
        if organization_data.description:
            organization_instance.description = organization_data.description
        if organization_data.contact:
            organization_instance.contact_email = organization_data.contact
        if organization_data.homepage:
            organization_instance.homepage = organization_data.homepage
        if organization_data.logo:
            organization_instance.logo = organization_data.logo
        organization_instance.save()

        return PatchOrganization(organization=organization_instance)


class Mutation(graphene.ObjectType):
    create_organization = CreateOrganization.Field()
    update_organization = UpdateOrganization.Field()
    patch_organization = PatchOrganization.Field()
    approve_reject_organization_approval = ApproveRejectOrganizationApproval.Field()
