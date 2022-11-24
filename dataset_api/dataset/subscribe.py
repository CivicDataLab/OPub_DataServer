import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from dataset_api.decorators import validate_token
from dataset_api.enums import SubscriptionAction
from dataset_api.models import Subscribe, Dataset


class SubscribeType(DjangoObjectType):
    class Meta:
        model = Subscribe
        fields = "__all__"


class Query(graphene.ObjectType):
    all_subscriptions = graphene.List(SubscribeType)
    user_subscriptions = graphene.List(SubscribeType)
    subscribe = graphene.Field(SubscribeType, subscribe_id=graphene.Int())
    user_dataset_subscription = graphene.Field(SubscribeType, dataset_id=graphene.Int())

    def resolve_all_subscriptions(self, info, **kwargs):
        return Subscribe.objects.all().order_by("-modified")

    def resolve_subscribe(self, info, subscribe_id):
        return Subscribe.objects.get(pk=subscribe_id)

    @validate_token
    def resolve_user_subscriptions(self, username):
        return Subscribe.objects.filter(username=username)

    @validate_token
    def resolve_user_dataset_subscription(self, info, dataset_id, username="", **kwargs):
        dataset = Dataset.objects.get(id=dataset_id)
        return Subscribe.objects.get(Q(user=username), Q(dataset=dataset))


class SubscribeInput(graphene.InputObjectType):
    dataset_id = graphene.ID(required=True)
    action = graphene.Enum.from_enum(SubscriptionAction)(required=True)


class SubscribeMutation(Output, graphene.Mutation):
    class Arguments:
        subscribe_input = SubscribeInput(required=True)

    success = graphene.Boolean()

    @validate_token
    def mutate(root, info, subscribe_input: SubscribeInput = None, username=""):
        dataset = Dataset.objects.get(id=subscribe_input.dataset_id)
        try:
            subscribe_instance = Subscribe.objects.get(user=username, dataset=dataset)
        except Subscribe.DoesNotExist as e:
            subscribe_instance = Subscribe(dataset=dataset, user=username)
        if subscribe_input.action == SubscriptionAction.UNSUBSCRIBE:
            subscribe_instance.delete()
        return SubscribeMutation(success=True)


class Mutation(graphene.ObjectType):
    subscribe_mutation = SubscribeMutation.Field()
