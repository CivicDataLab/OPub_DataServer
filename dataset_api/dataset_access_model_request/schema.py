import datetime

import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from django.db.models import Q
from graphql import GraphQLError

from dataset_api.models.DatasetAccessModelRequest import DatasetAccessModelRequest
from dataset_api.models.DatasetAccessModel import DatasetAccessModel
from dataset_api.decorators import (
    validate_token,
    validate_token_or_none,
    auth_user_by_org,
)
from .decorators import auth_query_dam_request
from ..enums import ValidationUnits


class DataAccessModelRequestType(DjangoObjectType):
    class Meta:
        model = DatasetAccessModelRequest
        fields = "__all__"


class DataAccessModelRequestStatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PurposeType(graphene.Enum):
    EDUCATION = "EDUCATION"
    RESEARCH = "RESEARCH"
    PERSONAL = "PERSONAL"
    OTHERS = "OTHERS"


class Query(graphene.ObjectType):
    all_data_access_model_requests = graphene.List(DataAccessModelRequestType)
    data_access_model_request = graphene.Field(
        DataAccessModelRequestType, data_access_model_request_id=graphene.Int()
    )
    data_access_model_request_user = graphene.List(DataAccessModelRequestType)
    data_access_model_request_org = graphene.List(
        DataAccessModelRequestType, org_id=graphene.Int()
    )
    validity = graphene.String()

    # Access : PMU
    @auth_user_by_org(action="query")
    def resolve_all_data_access_model_requests(self, info, role, **kwargs):
        if role == "PMU":
            return DatasetAccessModelRequest.objects.all().order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU/DPA of that org.
    @auth_query_dam_request(action="query||request_id")
    def resolve_data_access_model_request(
            self, info, data_access_model_request_id, role
    ):
        if role == "PMU" or role == "DPA":
            return DatasetAccessModelRequest.objects.get(
                pk=data_access_model_request_id
            )
        else:
            raise GraphQLError("Access Denied")

    @validate_token
    def resolve_data_access_model_request_user(self, info, username, **kwargs):
        return DatasetAccessModelRequest.objects.filter(user=username).order_by(
            "-modified"
        )

    # Access : PMU/DPA of that org.
    @auth_user_by_org(action="query")
    def resolve_data_access_model_request_org(self, info, role):
        if role == "PMU" or role == "DPA":
            org_id = info.context.headers.get("HTTP_ORGANIZATION")
            return DatasetAccessModelRequest.objects.filter(
                Q(access_model_id__data_access_model__organization=org_id),
                Q(status__exact="APPROVED"),
            )
        else:
            raise GraphQLError("Access Denied")

    @validate_token_or_none
    def resolve_validity(self: DatasetAccessModelRequest, info, username):
        if self.status == "APPROVED":
            validity = (
                self.access_model.data_access_model.validation
            )
            validity_unit = (
                self.access_model.data_access_model.validation_unit
            )
            approval_date = self.modified
            validation_deadline = approval_date
            if validity_unit == ValidationUnits.DAY:
                validation_deadline = approval_date + datetime.timedelta(days=validity)
            elif validity_unit == ValidationUnits.WEEK:
                validation_deadline = approval_date + datetime.timedelta(weeks=validity)
            elif validity_unit == ValidationUnits.MONTH:
                validation_deadline = approval_date + datetime.timedelta(days=(30 * validity))
            elif validity_unit == ValidationUnits.YEAR:
                validation_deadline = approval_date + datetime.timedelta(days=(365 * validity))
            return validation_deadline.strftime("%d-%m-%Y")
        else:
            return None


class DataAccessModelRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    description = graphene.String(required=True)
    access_model = graphene.ID(required=True)
    purpose = PurposeType(required=True)
    username = graphene.String(required=False)
    user_email = graphene.String(required=False)


class DataAccessModelRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = DataAccessModelRequestStatusType()
    remark = graphene.String(required=False)


def create_dataset_access_model_request(
        access_model, description, purpose, username, status="REQUESTED", user_email=None
):
    data_access_model_request_instance = DatasetAccessModelRequest(
        status=status,
        purpose=purpose,
        description=description,
        user=username,
        access_model=access_model,
        user_email=user_email,
    )
    data_access_model_request_instance.save()
    access_model.save()
    return data_access_model_request_instance


class DataAccessModelRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_access_model_request = DataAccessModelRequestInput()

    data_access_model_request = graphene.Field(DataAccessModelRequestType)

    @staticmethod
    @validate_token_or_none
    def mutate(
            root,
            info,
            data_access_model_request: DataAccessModelRequestInput = None,
            username=None,
    ):
        # TODO: fix magic strings
        purpose = data_access_model_request.purpose
        description = data_access_model_request.description
        access_model = DatasetAccessModel.objects.get(
            id=data_access_model_request.access_model
        )
        if not username:
            username = data_access_model_request.username
        data_access_model_request_instance = create_dataset_access_model_request(
            access_model,
            description,
            purpose,
            username,
            user_email=data_access_model_request.user_email,
        )
        return DataAccessModelRequestMutation(
            data_access_model_request=data_access_model_request_instance
        )


class ApproveRejectDataAccessModelRequest(graphene.Mutation, Output):
    class Arguments:
        data_access_model_request = DataAccessModelRequestUpdateInput()

    data_access_model_request = graphene.Field(DataAccessModelRequestType)

    @staticmethod
    def mutate(
            root, info, data_access_model_request: DataAccessModelRequestUpdateInput = None
    ):
        try:
            data_access_model_request_instance = DatasetAccessModelRequest.objects.get(
                id=data_access_model_request.id
            )
        except DatasetAccessModelRequest.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Data Access Model with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        data_access_model_request_instance.status = data_access_model_request.status
        if data_access_model_request.remark:
            data_access_model_request_instance.remark = data_access_model_request.remark
        data_access_model_request_instance.save()
        return ApproveRejectDataAccessModelRequest(
            data_access_model_request=data_access_model_request_instance
        )


class Mutation(graphene.ObjectType):
    data_access_model_request = DataAccessModelRequestMutation.Field()
    approve_reject_data_access_model_request = (
        ApproveRejectDataAccessModelRequest.Field()
    )
