import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphene_file_upload.scalars import Upload

from .models import Resource, DataRequest

class DataRequestType(DjangoObjectType):
    class Meta:
        model = DataRequest
        fields = "__all__"

class StatusType(graphene.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FULFILLED = "FULFILLED"
    FETCHED = "FETCHED"
class PurposeType(graphene.Enum):
    EDUCATION = "EDUCATION"
    RESEARCH = "RESEARCH"
    PERSONAL = "PERSONAL"
    OTHERS = "OTHERS"

class DataRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    status = StatusType()
    purpose = PurposeType()
    description = graphene.String(required=True)
    remark = graphene.String(required=False)
    file = Upload(required=False)
    resource_list = graphene.List(of_type=graphene.String, required=True)

class DataRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = StatusType()
    remark = graphene.String(required=False)
    file = Upload(required=False)

class DataRequestMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestInput()

    data_request = graphene.Field(DataRequestType)

    @staticmethod
    def mutate(root, info, data_request: DataRequestInput = None):
        
        # To do: Check if resource id's provided exists!!
        data_request_instance = DataRequest(
            status = data_request.status,
            description = data_request.description,
            remark = data_request.remark,
            purpose = data_request.purpose,
            file = data_request.file
        )
        data_request_instance.save()
        for ids in data_request.resource_list:
            try:
                resource_id = Resource.objects.get(id=int(ids))
                data_request_instance.resource.add(resource_id)
            except Resource.DoesNotExist as e:
                pass
        
        return DataRequestMutation(data_request=data_request_instance)

class DataRequestUpdateMutation(graphene.Mutation, Output):
    class Arguments:
        data_request = DataRequestUpdateInput()

    data_request = graphene.Field(DataRequestType)
    
    @staticmethod
    def mutate(root, info, data_request: DataRequestUpdateInput = None):
        data_request_instance = DataRequest.objects.get(id=data_request.id)
        if data_request_instance:
            data_request_instance.status = data_request.status
            data_request_instance.remark = data_request.remark
            data_request_instance.file = data_request.file
        data_request_instance.save()
        return DataRequestUpdateMutation(data_request=data_request_instance)