import graphene
from graphene_django import DjangoObjectType

from activity_log.models import Activity
from dataset_api.models import Organization, Dataset
from dataset_api.utils import dataset_slug


class ActivityType(DjangoObjectType):
    passed_time = graphene.String()
    target_type = graphene.String()
    slug = graphene.String()

    class Meta:
        model = Activity
        fields = "__all__"

    def resolve_passed_time(self: Activity, info):
        return self.timesince()

    def resolve_target_type(self: Activity, info):
        return str(self.target_content_type).split("|")[1].strip()

    def resolve_slug(self: Activity, info):
        target_type = str(self.target_content_type).split("|")[1].strip()
        if target_type == 'dataset':
            return dataset_slug(self.target_object_id)
        return None


class Query(graphene.ObjectType):
    org_activity = graphene.List(ActivityType, organization_id=graphene.ID())
    user_activity = graphene.List(ActivityType, user=graphene.String())

    def resolve_org_activity(self, info, organization_id):
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return {"success": False,
                    "errors": {"organization_id": [{"message": "Organization id not found", "code": "404"}]}}
        return Activity.objects.target_group(organization)

    def resolve_user_activity(self, info, user):
        return Activity.objects.actor(user)
