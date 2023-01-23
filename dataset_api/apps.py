from django.apps import AppConfig


class DatasetApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dataset_api"

    def ready(self):
        from activity_log.registry import register
        from dataset_api.models import (
            Dataset,
            Resource,
            Organization,
            OrganizationCreateRequest,
            License,
            DatasetAccessModelRequest,
            DataAccessModel,
            DataRequest,
            Subscribe,
            DatasetRatings
        )

        register(Dataset)
        register(Resource)
        register(Organization)
        register(OrganizationCreateRequest)
        register(DatasetAccessModelRequest)
        register(License)
        register(DataAccessModel)
        register(DataRequest)
        register(Subscribe)
        register(DatasetRatings)
