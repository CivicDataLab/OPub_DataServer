import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from dataset_api.data_access_model.contract import create_agreement
from dataset_api.dataset_access_model_request.schema import create_dataset_access_model_request, PurposeType
from dataset_api.decorators import validate_token, validate_token_or_none
from dataset_api.license.enums import AgreementStatus
from dataset_api.models import Agreement, DatasetAccessModel


class AgreementType(DjangoObjectType):
    class Meta:
        model = Agreement
        fields = "__all__"


class AgreementInput(graphene.InputObjectType):
    dataset_access_model = graphene.ID(required=True)
    # TODO: change to dataset_access_model_request_id
    id = graphene.ID(required=False)
    description = graphene.String(required=False, default="")
    purpose = PurposeType(required=False, default="OTHERS")
    username = graphene.String(required=False, default="")
    user_email = graphene.String(required=False, default="")


class AgreementMutation(graphene.Mutation, Output):
    class Arguments:
        agreement_request = AgreementInput()

    agreement = graphene.Field(AgreementType)

    @staticmethod
    @validate_token_or_none
    def mutate(root, info, agreement_request: AgreementInput, username):
        dataset_access_model = DatasetAccessModel.objects.get(id=agreement_request.dataset_access_model)
        status = "REQUESTED" if dataset_access_model.data_access_model.type == "RESTRICTED" else "APPROVED"
        # TODO: Add check for open dam
        if not username:
            username = agreement_request.username
        dataset_access_model_request = create_dataset_access_model_request(access_model=dataset_access_model,
                                                                           description=agreement_request.description,
                                                                           purpose=agreement_request.purpose,
                                                                           username=username,
                                                                           status=status,
                                                                           user_email=agreement_request.user_email,
                                                                           id=agreement_request.id)
        agreement_instance = Agreement(dataset_access_model=dataset_access_model, username=username,
                                       status=AgreementStatus.ACCEPTED.value,
                                       dataset_access_model_request=dataset_access_model_request,
                                       user_email=agreement_request.user_email)

        agreement_instance.save()
        create_agreement(dataset_access_model, username, agreement_instance)
        return AgreementMutation(agreement=agreement_instance)


class Mutation(graphene.ObjectType):
    agreement_request = AgreementMutation.Field()
