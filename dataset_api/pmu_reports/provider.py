import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_auth.bases import Output

from activity_log.signal import activity
from dataset_api.constants import IMAGE_FORMAT_MAPPING
from dataset_api.decorators import (
    validate_token,
    validate_token_or_none,
    create_user_org,
    auth_user_by_org,
    auth_request_org,
    modify_org_status,
    get_user_org,
    get_child_orgs_dpa,
)

from .decorators import (
    auth_get_all_users
)
from dataset_api.enums import (
    OrganizationTypes,
    OrganizationCreationStatusType,
    OrganizationSubTypes,
)
from dataset_api.file_utils import file_validation
from dataset_api.models import (
    Organization,
    OrganizationCreateRequest,
    Catalog,
    Resource,
    Dataset,
    Sector,
    DatasetAccessModelRequest,
    DatasetAccessModel,
    Geography,
    DatasetRatings,
    OrgDpaHistory,
)

from dataset_api.utils import get_client_ip, get_average_rating, log_activity
from dataset_api.email_utils import register_dpa_notif, org_create_notif
from dataset_api.dataset.schema import DatasetType
from dataset_api.organization_schema import OrgDpaType

'''class OrganizationType(DjangoObjectType):
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


class OrgItem(graphene.ObjectType):
    org_id = graphene.String()
    title = graphene.String()
    parent = graphene.List(graphene.String)'''
    
class ProviderItem(graphene.ObjectType):
    provider_user_name = graphene.String()
    provider_name = graphene.String()
    provider_email = graphene.String() 
    org_id = graphene.String()
    org_title = graphene.String()
    updated = graphene.String() 
    dpa_name = graphene.String()
    dpa_email = graphene.String()
    dataset_count = graphene.Int() 
    dataset_list = graphene.List(DatasetType)

class ProviderAdminItem(graphene.ObjectType):
    provider_user_name = graphene.String()
    provider_name = graphene.String()
    provider_email = graphene.String()
    org_id = graphene.String()
    org_title = graphene.String()
    updated = graphene.String()
    dp_count = graphene.Int()
    user_org_dataset_count = graphene.Int()
    org_dataset_count = graphene.Int()
    cdo_notif = graphene.String()
    dpa_list = graphene.List(OrgDpaType)

class UserItem(graphene.ObjectType):
    username = graphene.String()
    name = graphene.String()
    email = graphene.String() 
    first_name = graphene.String()
    date_joined = graphene.String()
    dataset_access_count = graphene.Int()
    ratings_user = graphene.Int()
    dataset_list = graphene.List(DatasetType)

class Query(graphene.ObjectType):
    # all_organizations = graphene.List(OrganizationType)
    # organization_by_id = graphene.Field(
    #     OrganizationType, organization_id=graphene.Int()
    # )
    # organization_by_tid = graphene.Field(
    #     OrganizationType, organization_tid=graphene.Int()
    # )
    # organization_by_title = graphene.List(
    #     OrganizationType, organization_title=graphene.String()
    # )
    # organizations = graphene.List(OrganizationType)

    # requested_rejected_organizations = graphene.List(OrganizationType)
    # organizations_by_user = graphene.List(OrganizationType)
    # organization_without_dpa = graphene.List(
    #     OrganizationType, organization_id=graphene.Int()
    # )
    # entity_by_state = graphene.List(
    #     OrganizationType,
    #     state=graphene.String(),
    #     entity_type=graphene.String(),
    #     parent_id=graphene.String(),
    # )
    # ministries_by_state = graphene.List(OrganizationType, state=graphene.String())
    # dept_by_ministry = graphene.List(
    #     OrganizationType, state=graphene.String(), organization_id=graphene.Int()
    # )
    # all_organizations_hierarchy = graphene.List(OrgItem)
    
    all_providers         = graphene.List(ProviderItem, org_id=graphene.Int(required=False))
    
    all_provider_admins   = graphene.List(ProviderAdminItem)
    
    all_users   = graphene.List(UserItem)

    # # : Allow all org list for PMU? Current State -- YES
    # @auth_user_by_org(action="query")
    # def resolve_all_organizations(self, info, role, **kwargs):
    #     if role == "PMU":
    #         return Organization.objects.all().order_by("-modified")
    #     else:
    #         raise GraphQLError("Access Denied")

    # # Access : DPA of that org.
    # @auth_user_by_org(action="query")
    # def resolve_organization_by_id(self, info, role, organization_id):
    #     if role == "DPA" or role == "PMU" or role == "DP":
    #         return Organization.objects.get(pk=organization_id)
    #     else:
    #         raise GraphQLError("Access Denied")

    # # Used only in Script for updating dpa information.
    # @auth_user_by_org(action="query")
    # def resolve_organization_by_tid(self, info, role, organization_tid):
    #     if role == "DPA" or role == "PMU" or role == "DP":
    #         return Organization.objects.get(
    #             organizationcreaterequest__ogd_tid=organization_tid
    #         )
    #     else:
    #         raise GraphQLError("Access Denied")

    # # Access : PMU or DPA of that org.
    # @auth_user_by_org(action="query")
    # @get_child_orgs_dpa
    # def resolve_organization_without_dpa(self, info, role, organization_id, **kwargs):
    #     if role == "DPA" or role == "PMU":
    #         return Organization.objects.filter(pk__in=kwargs["org_without_dpa"])
    #     else:
    #         raise GraphQLError("Access Denied")

    # # Access : All
    # def resolve_organization_by_title(self, info, organization_title, **kwargs):
    #     return Organization.objects.filter(
    #         Q(title__iexact=organization_title),
    #         Q(
    #             organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
    #         ),
    #     )

    # # Access : All
    # def resolve_organizations(self, info, **kwargs):
    #     return Organization.objects.filter(
    #         organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
    #     ).order_by("-modified")

    # # Access : PMU
    # @auth_user_by_org(action="query")
    # def resolve_requested_rejected_organizations(self, info, role, **kwargs):
    #     if role == "PMU":
    #         return Organization.objects.filter(
    #             ~Q(
    #                 organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
    #             )
    #         ).order_by("-modified")
    #     else:
    #         raise GraphQLError("Access Denied")

    # @get_user_org
    # def resolve_organizations_by_user(self, info, org_ids, **kwargs):
    #     return Organization.objects.filter(
    #         organizationcreaterequest__organization_ptr_id__in=org_ids
    #     ).order_by("-modified")

    # def resolve_ministries_by_state(self, info, state):
    #     state_obj = Geography.objects.get(name=state)
    #     return Organization.objects.filter(
    #         organizationcreaterequest__organization_subtypes="MINISTRY",
    #         organizationcreaterequest__state=state_obj,
    #     )

    # def resolve_entity_by_state(self, info, state, entity_type, parent_id):
    #     state_obj = Geography.objects.get(name=state)
    #     if not parent_id:
    #         return Organization.objects.filter(
    #             organizationcreaterequest__organization_subtypes=entity_type,
    #             organizationcreaterequest__state=state_obj,
    #         )
    #     else:
    #         return Organization.objects.filter(
    #             organizationcreaterequest__organization_subtypes=entity_type,
    #             organizationcreaterequest__state=state_obj,
    #             parent_id=parent_id,
    #         )

    # def resolve_dept_by_ministry(self, info, state, organization_id):
    #     state_obj = Geography.objects.get(name=state)
    #     return Organization.objects.filter(
    #         parent_id=organization_id,
    #         organizationcreaterequest__state=state_obj,
    #     )

    # @auth_user_by_org(action="query")
    # def resolve_all_organizations_hierarchy(self, info, role, **kwargs):
    #     if role == "PMU":
    #         org_list = []
    #         organizations = OrganizationCreateRequest.objects.all().order_by(
    #             "-modified"
    #         )
    #         for org in organizations:
    #             if org.organization_subtypes in ["OTHER", "MINISTRY"]:
    #                 org_list.append(OrgItem(org.id, org.title, ["", "", ""]))
    #             if org.organization_subtypes in ["DEPARTMENT"]:
    #                 org_list.append(
    #                     OrgItem(
    #                         org.id,
    #                         org.title,
    #                         [
    #                             org.state.name if org.state else "",
    #                             "",
    #                             org.parent.title if org.parent else "",
    #                         ],
    #                     )
    #                 )
    #             if org.organization_subtypes in ["ORGANISATION"]:

    #                 temp_parent = [org.state.name if org.state else "", org.parent.parent.title if org.parent and org.parent.parent else "", org.parent.title if org.parent else ""]
    #                 temp_org = OrgItem(org.id, org.title, temp_parent)
    #                 org_list.append(temp_org)
    #         return org_list
    #     else:
    #         raise GraphQLError("Access Denied")
        
    @auth_get_all_users(role=["DP"])
    @auth_user_by_org(action="query")
    def resolve_all_providers(self, info, role, users=[], org_id=None):
        
        if role == "PMU":
            user_list = []
            #print ('-------------users', users)
            for user in users:
                for org in user['access']:
                    org_obj = OrganizationCreateRequest.objects.get(organization_ptr_id=org["org_id"])
                    dataset_obj = Dataset.objects.filter(id__in=org["dataset_list"], catalog__organization=org["org_id"], status="PUBLISHED")
                    user_obj = ProviderItem(user['username'], user['name'], user['email'], org['org_id'], org['org_title'],  org['updated'], org_obj.dpa_name, org_obj.dpa_email, dataset_obj.count(), dataset_obj)
                    if org_id and str(org_id) != org['org_id']:
                        pass
                    else:
                        user_list.append(user_obj) 
            return user_list
        else:
            raise GraphQLError("Access Denied")
        
    @auth_get_all_users(role=["DPA"])
    @auth_user_by_org(action="query")
    def resolve_all_provider_admins(self, info, role, users=[]):
        
        if role == "PMU":
            user_list = []
            #print ('-------------users', users)
            for user in users:
                for org in user['access']:
                    #print(org["dataset_list"], user["username"])
                    user_org_dataset_count = Dataset.objects.filter(id__in=org["dataset_list"], catalog__organization=org["org_id"], status="PUBLISHED").count()
                    org_dataset_count = Dataset.objects.filter(catalog__organization=org["org_id"], status="PUBLISHED").count()

                    #print(dataset_count, org["org_id"])
                    org_obj = OrganizationCreateRequest.objects.get(organization_ptr_id=org["org_id"])
                    dpa_list = OrgDpaHistory.objects.filter(org_id = org['org_id'])
                    user_obj = ProviderAdminItem(user['username'], user['name'], user['email'], org['org_id'], org['org_title'],  org['updated'], org['dp_count'], user_org_dataset_count, org_dataset_count, org_obj.cdo_notification, dpa_list)
                    user_list.append(user_obj)
            return user_list
        else:
            raise GraphQLError("Access Denied")     
        
    @auth_get_all_users(role=["All"])
    @auth_user_by_org(action="query")
    def resolve_all_users(self, info, role, users=[]):
        
        if role == "PMU":
            user_list = []
            print ('-------------users', users)
            for user in users:
                ratings_user = DatasetRatings.objects.filter(user = user['username'], status = "PUBLISHED").count()
                dataset_obj = Dataset.objects.filter(id__in=user["dataset_list"],  status="PUBLISHED")
                user_obj = UserItem(user['username'], user['name'], user['email'], user['name'], user['date_joined'], user['dataset_access_count'], ratings_user, dataset_obj)
                user_list.append(user_obj)
            return user_list
        else:
            raise GraphQLError("Access Denied")      

