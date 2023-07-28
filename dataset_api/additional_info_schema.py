import mimetypes
import magic
import graphene
from graphene import List
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .data_access_model.contract import update_provider_agreement
from .decorators import validate_token
from .models import Dataset, AdditionalInfo
from .constants import FORMAT_MAPPING


class AdditionalInfoType(DjangoObjectType):
    class Meta:
        model = AdditionalInfo
        fields = "__all__"


class Query(graphene.ObjectType):
    all_info = graphene.List(AdditionalInfoType)
    info = graphene.Field(AdditionalInfoType, info_id=graphene.Int())

    def resolve_all_info(self, info, **kwargs):
        return AdditionalInfo.objects.all()

    def resolve_info(self, info, additional_info_id):
        return AdditionalInfo.objects.get(pk=additional_info_id)


class InfoType(graphene.Enum):
    DATASTORY = "DATASTORY"
    REPORT = "REPORT"
    BLOG = "BLOG"
    USECASE = "USECASE"
    OTHER = "OTHER"


class AdditionalInfoInput(graphene.InputObjectType):
    id: str = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    file = Upload(required=False)
    dataset = graphene.String(required=True)
    format = graphene.String(required=False)
    remote_url = graphene.String(required=False)
    type = InfoType(required=False)
    policy_title = graphene.String(required=False)
    policy_url = graphene.String(required=False)
    license_title = graphene.String(required=False)
    license_url = graphene.String(required=False)


class CreateAdditionInfo(graphene.Mutation, Output):
    class Arguments:
        info_data = AdditionalInfoInput()

    resource = graphene.Field(AdditionalInfoType)

    @staticmethod
    @validate_token
    def mutate(root, info, info_data: AdditionalInfoInput = None, username=None):
        """

        :type info_data: List of dictionary
        """
        dataset = Dataset.objects.get(id=info_data.dataset)
        data_format = info_data.format

        info_instance = AdditionalInfo(
            title=info_data.title,
            description=info_data.description,
            dataset=dataset,
            format=data_format,
            remote_url=info_data.remote_url,
            type=info_data.type,
            file=info_data.file,
            policy_title=info_data.policy_title,
            policy_url=info_data.policy_url,
            license_title=info_data.license_title,
            license_url=info_data.license_url,
        )
        if data_format == "" and info_data.file:
            info_instance.format = FORMAT_MAPPING[magic.from_buffer(info_instance.file.read(), mime=True)[0]]
        info_instance.save()
        update_provider_agreement(dataset, username)
        return CreateAdditionInfo(success=True, resource=info_instance)


class UpdateAdditionalInfo(graphene.Mutation, Output):
    class Arguments:
        info_data = AdditionalInfoInput(required=True)

    additional_info = graphene.Field(AdditionalInfoType)

    @staticmethod
    @validate_token
    def mutate(root, info, info_data: AdditionalInfoInput = None, username=None):
        info_instance = AdditionalInfo.objects.get(id=int(info_data.id))
        dataset = Dataset.objects.get(id=info_data.dataset)
        if info_instance:
            info_instance.title = info_data.title
            info_instance.description = info_data.description
            info_instance.dataset = dataset
            info_instance.format = info_data.format
            info_instance.remote_url = info_data.remote_url
            info_instance.file = info_data.file
            info_instance.type = info_data.type
            info_instance.policy_title = info_data.policy_title
            info_instance.policy_url = info_data.policy_url
            info_instance.license_title = info_data.license_title
            info_instance.license_url = info_data.license_url
            
            if info_data.format == "" and info_data.file:
                info_instance.format = FORMAT_MAPPING.get(magic.from_buffer(info_instance.file.read(), mime=True)[0])

            info_instance.save()
            update_provider_agreement(dataset, username)
            return UpdateAdditionalInfo(success=True, additional_info=info_instance)
        return UpdateAdditionalInfo(success=False, additional_info=None)


class DeleteAdditionalInfo(graphene.Mutation, Output):
    class Arguments:
        id = graphene.ID()

    additional_info = graphene.Field(AdditionalInfoType)

    @staticmethod
    @validate_token
    def mutate(root, info, id, username=None):
        info_instance = AdditionalInfo.objects.get(id=id)
        info_instance.delete()
        update_provider_agreement(info_instance.dataset, username)
        return DeleteAdditionalInfo(success=True)


class Mutation(graphene.ObjectType):
    create_additional_info = CreateAdditionInfo.Field()
    update_additional_info = UpdateAdditionalInfo.Field()
    delete_additional_info = DeleteAdditionalInfo.Field()
