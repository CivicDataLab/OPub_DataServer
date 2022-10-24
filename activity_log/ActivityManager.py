from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Manager, Q
from django.db.models.query import EmptyQuerySet

from activity_log.decorators import stream


class GFKQuerySet(QuerySet):
    """
    A QuerySet with a fetch_generic_relations() method to bulk fetch
    all generic related items.  Similar to select_related(), but for
    generic foreign keys. This wraps QuerySet.prefetch_related.
    """

    def fetch_generic_relations(self, *args):
        qs = self._clone()

        private_fields = self.model._meta.private_fields

        gfk_fields = [g for g in private_fields if isinstance(g, GenericForeignKey)]

        if args:
            gfk_fields = [g for g in gfk_fields if g.name in args]

        return qs.prefetch_related(*[g.name for g in gfk_fields])

    def _clone(self, klass=None, **kwargs):
        return super(GFKQuerySet, self)._clone()

    def none(self):
        clone = self._clone({'klass': EmptyGFKQuerySet})
        if hasattr(clone.query, 'set_empty'):
            clone.query.set_empty()
        return clone


class EmptyGFKQuerySet(GFKQuerySet, EmptyQuerySet):
    def fetch_generic_relations(self, *args):
        return self


class GFKManager(Manager):
    """
    A manager that returns a GFKQuerySet instead of a regular QuerySet.
    """

    def get_query_set(self):
        return GFKQuerySet(self.model)

    get_queryset = get_query_set

    def none(self):
        return self.get_queryset().none()


class ActivityManager(GFKManager):
    """
    Default manager for Actions, accessed through Activity.objects
    """

    def public(self, *args, **kwargs):
        kwargs['public'] = True
        return self.filter(*args, **kwargs)

    @stream
    def actor(self, obj, **kwargs):
        """
        Stream of most recent actions where obj is the actor.
        Keyword arguments will be passed to Action.objects.filter
        """
        # TODO: fix this
        kwargs['actor'] = obj
        return self.filter(**kwargs)

    @stream
    def target(self, obj, **kwargs):
        """
        Stream of most recent actions where obj is the target.
        Keyword arguments will be passed to Action.objects.filter
        """
        return obj.target_actions.public(**kwargs)

    @stream
    def target_group(self, obj, **kwargs):
        """
        Stream of most recent actions where obj is the target_group.
        Keyword arguments will be passed to Action.objects.filter
        """
        return obj.target_group_actions.public(**kwargs)

    @stream
    def action_object(self, obj, **kwargs):
        """
        Stream of most recent actions where obj is the action_object.
        Keyword arguments will be passed to Action.objects.filter
        """
        return obj.action_object_actions.public(**kwargs)

    @stream
    def model_actions(self, model, **kwargs):
        """
        Stream of most recent actions by any particular model
        """
        ctype = ContentType.objects.get_for_model(model)
        return self.public(
            (Q(target_content_type=ctype)
             | Q(action_object_content_type=ctype)
             | Q(target_group_content_type=ctype)),
            **kwargs
        )

    @stream
    def any(self, obj, **kwargs):
        """
        Stream of most recent actions where obj is the target OR action_object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.public(
            Q(
                target_content_type=ctype,
                target_object_id=obj.pk,
            ) | Q(
                target_group_content_type=ctype,
                target_group_object_id=obj.pk,
            ) | Q(
                action_object_content_type=ctype,
                action_object_object_id=obj.pk,
            ), **kwargs)

    @stream
    def user(self, user, with_user_activity=False, follow_flag=None, **kwargs):
        """Create a stream of the most recent actions by objects that the user is following."""
        q = Q()
        qs = self.public()

        if not user:
            return qs.none()

        if with_user_activity:
            q = q | Q(
                actor_content_type=ContentType.objects.get_for_model(user),
                actor_object_id=user.pk
            )

        follows = apps.get_model('activity_log', 'follow').objects.filter(user=user)
        if follow_flag:
            follows = follows.filter(flag=follow_flag)

        content_types = ContentType.objects.filter(
            pk__in=follows.values('content_type_id')
        )

        if not (content_types.exists() or with_user_activity):
            return qs.none()

        for content_type in content_types:
            object_ids = follows.filter(content_type=content_type)
            q = q | Q(
                target_content_type=content_type,
                target_object_id__in=object_ids.filter(
                    actor_only=False).values('object_id')
            ) | Q(
                action_object_content_type=content_type,
                action_object_object_id__in=object_ids.filter(
                    actor_only=False).values('object_id')
            ) | Q(
                target_group_content_type=content_type,
                target_group_object_id__in=object_ids.filter(
                    actor_only=False).values('object_id')
            )

        return qs.filter(q, **kwargs)
