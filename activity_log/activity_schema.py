import graphene
from graphene_django import DjangoObjectType

from activity_log.models import Activity
from dataset_api.models import Organization, Dataset
from dataset_api.utils import dataset_slug


class ActivityType(DjangoObjectType):
    passed_time = graphene.String()
    target_type = graphene.String()
    slug = graphene.String()
    title = graphene.String()

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

    def resolve_title(self: Activity, info):
        if hasattr(self.target, "title"):
            return self.target.title


class Query(graphene.ObjectType):
    org_activity = graphene.List(ActivityType, organization_id=graphene.ID(), first=graphene.Int(),
                                 skip=graphene.Int())
    user_activity = graphene.List(ActivityType, user=graphene.String(), first=graphene.Int(),
                                  skip=graphene.Int(), )

    def resolve_org_activity(self, info, organization_id, first=None, skip=None):
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return {"success": False,
                    "errors": {"organization_id": [{"message": "Organization id not found", "code": "404"}]}}
        query = Activity.objects.target_group(organization)
        if skip:
            query = query[skip:]
        if first:
            query = query[:first]
        return query

    def resolve_user_activity(self, info, user, first=None, skip=None):
        query = Activity.objects.actor(user)
        if skip:
            query = query[skip:]
        if first:
            query = query[:first]
        return query
