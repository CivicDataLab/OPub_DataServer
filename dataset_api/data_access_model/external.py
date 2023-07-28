import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphql import GraphQLError

from activity_log.signal import activity
from ..decorators import validate_token
from ..models import ExternalAccessModel, Policy, License, Dataset
from ..utils import get_client_ip, log_activity
from .decorators import auth_user_action_dam

class ExternalAccessModelType(DjangoObjectType):
    class Meta:
        model = ExternalAccessModel
        fields = "__all__"


class Query(graphene.ObjectType):
    all_external_access_models = graphene.List(ExternalAccessModelType)
    external_access_model_by_dataset = graphene.Field(ExternalAccessModelType, dataset_id=graphene.ID())

    @validate_token
    def resolve_all_external_access_models(self, info, username, **kwargs):
        return ExternalAccessModel.objects.all().order_by("-modified")
    
    @validate_token
    def resolve_external_access_model_by_dataset(self, info, username, dataset_id, **kwargs):
        return ExternalAccessModel.objects.get(dataset=dataset_id)


class ExternalAccessModelInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    dataset = graphene.ID(required=True)
    license = graphene.ID(required=True)
    policy = graphene.ID(required=False)


class DeleteExternalAccessModelInput(graphene.InputObjectType):
    id = graphene.ID(required=True)


class CreateExternalAccessModel(Output, graphene.Mutation):
    class Arguments:
        external_access_model_data = ExternalAccessModelInput()

    external_access_model = graphene.Field(ExternalAccessModelType)

    @staticmethod
    @validate_token
    @auth_user_action_dam(action="create_dam")
    def mutate(
        root, info, username, external_access_model_data: ExternalAccessModelInput
    ):
        try:
            policy_instance = None
            dataset_instance = Dataset.objects.get(pk=external_access_model_data.dataset)
            license_instance = License.objects.get(pk=external_access_model_data.license)
            if external_access_model_data.policy:
                policy_instance = Policy.objects.get(pk=external_access_model_data.policy)
        except Dataset.DoesNotExist:
            raise GraphQLError("Dataset with given id does not exist.")
        except License.DoesNotExist:
            raise GraphQLError("License with given id does not exist.")
        except Policy.DoesNotExist:
            raise GraphQLError("Policy with given id does not exist.")
        
        if external_access_model_data.id:
            try:
                external_access_model_instance = ExternalAccessModel.objects.get(pk=external_access_model_data.id)
            except ExternalAccessModel.DoesNotExist:
                raise GraphQLError("Access Model with given id does not exist.")
            external_access_model_instance.license = license_instance
            external_access_model_instance.policy = policy_instance if policy_instance else None
            external_access_model_instance.save()
            
            log_activity(
                target_obj=external_access_model_instance,
                ip=get_client_ip(info),
                target_group=dataset_instance,
                username=username,
                verb="Updated",
                )
        else:
            external_access_model_instance = ExternalAccessModel(
                dataset=dataset_instance,
                license=license_instance,
                policy=policy_instance if policy_instance else None,
            )
            external_access_model_instance.save()

            log_activity(
                target_obj=external_access_model_instance,
                ip=get_client_ip(info),
                target_group=dataset_instance,
                username=username,
                verb="Created",
                )
        return CreateExternalAccessModel(
            external_access_model=external_access_model_instance
        )

class DeleteExternalAccessModel(Output, graphene.Mutation):
    class Arguments:
        external_access_model_data = DeleteExternalAccessModelInput()

    success = graphene.String()

    @staticmethod
    @validate_token
    @auth_user_action_dam(action="delete_dam")
    def mutate(
        root, info, username, external_access_model_data: ExternalAccessModelInput
    ):
        try:
            external_access_model_instance = ExternalAccessModel.objects.get(pk=external_access_model_data.id)
        except ExternalAccessModel.DoesNotExist:
            raise GraphQLError("Access Model with given id does not exist.")
        
        log_activity(
            target_obj=external_access_model_instance,
            ip=get_client_ip(info),
            target_group=external_access_model_instance.dataset,
            username=username,
            verb="Deleted",
        )
        external_access_model_instance.delete()
        return DeleteExternalAccessModel(success=True)


class Mutation(graphene.ObjectType):
    create_external_access_model = CreateExternalAccessModel.Field()
    delete_external_access_model = DeleteExternalAccessModel.Field()
