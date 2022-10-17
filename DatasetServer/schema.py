import graphene
import dataset_api.dataset_schema
import dataset_api.organization_schema
import dataset_api.catalog_schema
import dataset_api.resource_schema
import dataset_api.tag_schema
import dataset_api.geography_schema
import dataset_api.sector_schema
import dataset_api.api_source_schema
import dataset_api.additional_info_schema
import dataset_api.rating_schema
import dataset_api.data_access_model.data_request_schema
import dataset_api.data_access_model.schema
import dataset_api.dataset_moderation
import dataset_api.data_access_model.data_access_model_request_schema
import dataset_api.data_access_model.access_model_resource_schema
import dataset_api.license_schema
import dataset_api.stats_schema


class Query(dataset_api.dataset_schema.Query, dataset_api.organization_schema.Query, dataset_api.catalog_schema.Query,
            dataset_api.resource_schema.Query, dataset_api.tag_schema.Query, dataset_api.geography_schema.Query,
            dataset_api.api_source_schema.Query, dataset_api.rating_schema.Query, dataset_api.license_schema.Query,
            dataset_api.sector_schema.Query, dataset_api.additional_info_schema.Query,
            dataset_api.data_access_model.data_request_schema.Query, dataset_api.data_access_model.access_model_resource_schema.Query,
            dataset_api.data_access_model.schema.Query, dataset_api.dataset_moderation.Query,
            dataset_api.data_access_model.data_access_model_request_schema.Query, dataset_api.stats_schema.Query,
            graphene.ObjectType):
    pass


class Mutation(dataset_api.dataset_schema.Mutation, dataset_api.organization_schema.Mutation,
               dataset_api.catalog_schema.Mutation,
               dataset_api.resource_schema.Mutation, dataset_api.tag_schema.Mutation,
               dataset_api.geography_schema.Mutation,
               dataset_api.api_source_schema.Mutation, dataset_api.rating_schema.Mutation,
               dataset_api.license_schema.Mutation,
               dataset_api.sector_schema.Mutation, dataset_api.additional_info_schema.Mutation,
               dataset_api.data_access_model.data_request_schema.Mutation,
               dataset_api.data_access_model.schema.Mutation, dataset_api.dataset_moderation.Mutation,
               dataset_api.data_access_model.data_access_model_request_schema.Mutation,
               dataset_api.data_access_model.access_model_resource_schema.Mutation,
               graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
