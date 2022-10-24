from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.timesince import timesince as djtimesince
from django.utils.timezone import now
from django.utils.translation import gettext as _

from activity_log.ActivityManager import ActivityManager
from activity_log.FollowManager import FollowManager


class Activity(models.Model):
    # actor_content_type = models.ForeignKey(
    #     ContentType, related_name='actor',
    #     on_delete=models.CASCADE, db_index=True
    # )
    actor = models.CharField(max_length=255, db_index=True)
    # actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)

    target_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='target',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    target = GenericForeignKey(
        'target_content_type',
        'target_object_id'
    )

    target_group_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='target_group',
        on_delete=models.CASCADE, db_index=True
    )
    target_group_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    target_group = GenericForeignKey(
        'target_group_content_type',
        'target_group_object_id'
    )

    action_object_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='action_object',
        on_delete=models.CASCADE, db_index=True
    )
    action_object_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    action_object = GenericForeignKey(
        'action_object_content_type',
        'action_object_object_id'
    )

    issued = models.DateTimeField(default=now, db_index=True)

    public = models.BooleanField(default=True, db_index=True)

    objects = ActivityManager()

    class Meta:
        ordering = ('-issued',)

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'target_group': self.target_group,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return _('%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago') % ctx
            return _('%(actor)s %(verb)s %(target)s %(timesince)s ago') % ctx
        if self.action_object:
            return _('%(actor)s %(verb)s %(action_object)s %(timesince)s ago') % ctx
        return _('%(actor)s %(verb)s %(timesince)s ago') % ctx

    def actor_url(self):
        # TODO: fix this based on the the user landing
        return "http://Actor"
        # return reverse('actstream_actor', None,
        #                (self.actor_content_type.pk, self.actor_object_id))

    def target_url(self):
        # TODO: fix views
        return reverse('actstream_actor', None,
                       (self.target_content_type.pk, self.target_object_id))

    def action_object_url(self):
        # TODO: fix views
        return reverse('actstream_actor', None, (
            self.action_object_content_type.pk, self.action_object_object_id))

    def timesince(self, now=None):
        return djtimesince(self.issued, now).encode('utf8').replace(b'\xc2\xa0', b' ').decode('utf8')

    def get_absolute_url(self):
        # TODO: fix views
        return reverse(
            'actstream_detail', args=[self.pk])


class Follow(models.Model):
    """
    Lets a user follow the activities of any specific actor
    """
    user = models.CharField(max_length=255, db_index=True)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, db_index=True
    )
    object_id = models.CharField(max_length=255, db_index=True)
    follow_object = GenericForeignKey()
    actor_only = models.BooleanField(
        "Only follow actions where "
        "the object is the target.",
        default=True
    )
    flag = models.CharField(max_length=255, blank=True, db_index=True, default='')
    started = models.DateTimeField(default=now, db_index=True)
    objects = FollowManager()

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', 'flag')

    def __str__(self):
        return '{} -> {} : {}'.format(self.user, self.follow_object, self.flag)
