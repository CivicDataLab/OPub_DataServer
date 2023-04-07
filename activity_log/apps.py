from django.apps import AppConfig

from activity_log.signal import activity


class ActivityLogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_log'
    verbose_name = 'Activity Logs'

    def ready(self):
        from activity_log.actions import activity_handler
        activity.connect(activity_handler, dispatch_uid='activity_log.models')
