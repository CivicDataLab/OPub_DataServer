from django.apps import AppConfig


class DatasetApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dataset_api'

    def ready(self):
        from activity_log.registry import register
        from dataset_api.models import Dataset, Resource, Organization
        register(Dataset)
        register(Resource)
        register(Organization)
