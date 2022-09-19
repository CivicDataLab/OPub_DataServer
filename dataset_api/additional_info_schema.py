import mimetypes

import graphene
from graphene import List
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import Dataset, AdditionalInfo
from .utils import FORMAT_MAPPING


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


class AdditionalInfoInput(graphene.InputObjectType):
    id: str = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=False)
    file = Upload(required=False)
    dataset = graphene.String(required=True)
    format = graphene.String(required=False)
    remote_url = graphene.String(required=False)
    type = InfoType()


class CreateAdditionInfo(graphene.Mutation, Output):
    class Arguments:
        info_data = AdditionalInfoInput()

    resource = graphene.Field(AdditionalInfoType)

    @staticmethod
    def mutate(root, info, info_data: AdditionalInfoInput = None):
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
        )
        if data_format == "":
            info_instance.format = FORMAT_MAPPING[mimetypes.guess_type(info_instance.file.path)[0]]
        info_instance.save()
        return CreateAdditionInfo(success=True, resource=info_instance)


class UpdateAdditionalInfo(graphene.Mutation, Output):
    class Arguments:
        resource_data = AdditionalInfoInput(required=True)

    additional_info = graphene.Field(AdditionalInfoType)

    @staticmethod
    def mutate(root, info, info_data: AdditionalInfoInput = None):
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
            if info_data.format == "":
                info_instance.format = FORMAT_MAPPING.get(mimetypes.guess_type(info_instance.file.path)[0])

            info_instance.save()
            return UpdateAdditionalInfo(success=True, additional_info=info_instance)
        return UpdateAdditionalInfo(success=False, additional_info=None)


class DeleteAdditionalInfo(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    additional_info = graphene.Field(AdditionalInfoType)

    @staticmethod
    def mutate(root, info, id):
        info_instance = AdditionalInfo.objects.get(id=id)
        info_instance.delete()
        return DeleteAdditionalInfo(success=True, additional_info=info_instance)
