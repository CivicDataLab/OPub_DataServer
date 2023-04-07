import graphene
from graphene_django import DjangoObjectType

from activity_log.models import Activity
from dataset_api.models import Organization
from dataset_api.utils import dataset_slug
from datetime import datetime, timezone

class FieldTypes(graphene.Enum):
    ip = "ip"
    actor = "actor"
    browser = "browser"
    verb = "verb"


class ActivityFilter(graphene.InputObjectType):
    type = FieldTypes()
    value = graphene.String()


class ActivityType(DjangoObjectType):
    passed_time = graphene.String()
    target_type = graphene.String()
    slug = graphene.String()
    target_title = graphene.String()
    dtf_passed_time = graphene.String()

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

    def resolve_target_title(self: Activity, info):
        if hasattr(self.target, "title"):
            return self.target.title
    
    def resolve_dtf_passed_time(self: Activity, info):
        # dtf = datetime.now(timezone.utc) - self.issued
        dtf = self.issued.strftime("%H:%M %p, %d %b %Y ")
        return dtf


def add_pagination_filters(first, query, skip):
    if skip:
        query = query[skip:]
    if first:
        query = query[:first]
    return query


def get_filter_args(filters):
    kwargs = {}
    for filter in filters:
        kwargs[filter.type] = filter.value
    return kwargs


class Query(graphene.ObjectType):
    org_activity = graphene.List(ActivityType, organization_id=graphene.ID(), first=graphene.Int(),
                                 skip=graphene.Int(),
                                 filters=graphene.Argument(type=graphene.List(of_type=ActivityFilter), required=False))
    user_activity = graphene.List(ActivityType, user=graphene.String(), first=graphene.Int(),
                                  skip=graphene.Int(),
                                  filters=graphene.Argument(graphene.List(of_type=ActivityFilter), required=False))

    def resolve_org_activity(self, info, organization_id, filters: [ActivityFilter] = [], first=None, skip=None):
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return {"success": False,
                    "errors": {"organization_id": [{"message": "Organization id not found", "code": "404"}]}}
        kwargs = get_filter_args(filters)
        query = Activity.objects.target_group(organization, **kwargs)
        query = add_pagination_filters(first, query, skip)
        return query

    def resolve_user_activity(self, info, user, filters: [ActivityFilter] = [], first=None, skip=None):
        query = Activity.objects.actor(user)
        kwargs = get_filter_args(filters)
        query = Activity.objects.actor(user, **kwargs)
        query = add_pagination_filters(first, query, skip)
        return query
