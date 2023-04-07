from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from activity_log.ActivityManager import GFKManager


class FollowManager(GFKManager):
    """
    Manager for Follow model.
    """

    def for_object(self, instance, flag=''):
        """
        Filter to a specific instance.
        """
        content_type = ContentType.objects.get_for_model(instance).pk
        queryset = self.filter(content_type=content_type, object_id=instance.pk)
        if flag:
            queryset = queryset.filter(flag=flag)
        return queryset

    def is_following(self, user, instance, flag=''):
        """
        Check if a user is following an instance.
        """
        if not user:
            return False
        queryset = self.for_object(instance)

        if flag:
            queryset = queryset.filter(flag=flag)
        return queryset.filter(user=user).exists()

    def followers(self, actor, flag=''):
        """
        Returns a list of User objects who are following the given actor (eg my followers).
        """
        return [follow.user for follow in self.followers_qs(actor, flag=flag)]

    def following_qs(self, user, *models, **kwargs):
        """
        Returns a queryset of actors that the given user is following (eg who im following).
        Items in the list can be of any model unless a list of restricted models are passed.
        Eg following(user, User) will only return users following the given user
        """
        qs = self.filter(user=user)
        ctype_filters = Q()
        for model in models:
            ctype_filters |= Q(content_type=ContentType.objects.get_for_model(model))
        qs = qs.filter(ctype_filters)

        flag = kwargs.get('flag', '')

        if flag:
            qs = qs.filter(flag=flag)
        return qs.fetch_generic_relations('follow_object')

    def following(self, user, *models, **kwargs):
        """
        Returns a list of actors that the given user is following (eg who im following).
        Items in the list can be of any model unless a list of restricted models are passed.
        Eg following(user, User) will only return users following the given user
        """
        return [follow.follow_object for follow in self.following_qs(
            user, *models, flag=kwargs.get('flag', '')
        )]
