from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType

# from actstream import settings
# from actstream.signals import action
# from actstream.registry import check
from activity_log.signal import activity


def follow(user, obj, send_action=True, actor_only=True, flag='', **kwargs):
    instance, created = apps.get_model('activity_log', 'follow').objects.get_or_create(
        user=user, object_id=obj.pk, flag=flag,
        content_type=ContentType.objects.get_for_model(obj),
        actor_only=actor_only
    )
    if send_action and created:
        if not flag:
            activity.send(user, verb=_('started following'), target=obj, **kwargs)
        else:
            activity.send(user, verb=_('started %s' % flag), target=obj, **kwargs)
    return instance


def unfollow(user, obj, send_action=False, flag=''):
    qs = apps.get_model('activity_log', 'follow').objects.filter(
        user=user, object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj)
    )

    if flag:
        qs = qs.filter(flag=flag)
    qs.delete()

    if send_action:
        if not flag:
            activity.send(user, verb=_('stopped following'), target=obj)
        else:
            activity.send(user, verb=_('stopped %s' % flag), target=obj)


def is_following(user, obj, flag=''):
    qs = apps.get_model('activity_log', 'follow').objects.filter(
        user=user, object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj)
    )

    if flag:
        qs = qs.filter(flag=flag)

    return qs.exists()


def activity_handler(verb, **kwargs):
    kwargs.pop('signal', None)
    actor = kwargs.pop('sender')

    new_activity = apps.get_model('activity_log', 'activity')(
        actor=actor,
        verb=str(verb),
        public=bool(kwargs.pop('public', True)),
        description=kwargs.pop('description', None),
        issued=kwargs.pop('issued', now()),
        ip=kwargs.pop('ip', None),
        browser=kwargs.pop('browser', None)
    )

    for opt in ('target', 'action_object', 'target_group'):
        obj = kwargs.pop(opt, None)
        if obj is not None:
            setattr(new_activity, '%s_object_id' % opt, obj.pk)
            setattr(new_activity, '%s_content_type' % opt,
                    ContentType.objects.get_for_model(obj))
    new_activity.save(force_insert=True)
    return new_activity
