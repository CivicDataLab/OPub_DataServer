import graphene
import dataset_api.dataset.schema
import dataset_api.organization_schema
import dataset_api.catalog_schema
import dataset_api.resource_schema
import dataset_api.tag_schema
import dataset_api.geography_schema
import dataset_api.sector_schema
import dataset_api.api_source_schema
import dataset_api.additional_info_schema
import dataset_api.rating_schema
import dataset_api.data_request.schema
import dataset_api.data_access_model.schema
import dataset_api.dataset_access_model.schema
import dataset_api.dataset_access_model_request.schema
import dataset_api.dataset_access_model_resource.schema
import dataset_api.license.license_schema
import dataset_api.stats_schema
import dataset_api.dataset_moderation
import dataset_api.organization_request_schema
import dataset_api.aggrements.schema
import dataset_api.license_addition.license_addition_schema

import activity_log.activity_schema


class Query(dataset_api.dataset.schema.Query, dataset_api.organization_schema.Query, dataset_api.catalog_schema.Query,
            dataset_api.resource_schema.Query, dataset_api.tag_schema.Query, dataset_api.geography_schema.Query,
            dataset_api.api_source_schema.Query, dataset_api.rating_schema.Query,
            dataset_api.license.license_schema.Query,
            dataset_api.sector_schema.Query, dataset_api.additional_info_schema.Query,
            dataset_api.data_request.schema.Query, dataset_api.dataset_access_model.schema.Query,
            dataset_api.dataset_access_model_request.schema.Query,
            dataset_api.data_access_model.schema.Query, dataset_api.dataset_moderation.Query,
            dataset_api.stats_schema.Query,
            dataset_api.organization_request_schema.Query,
            activity_log.activity_schema.Query,
            dataset_api.license_addition.license_addition_schema.Query,
            graphene.ObjectType):
    pass


class Mutation(dataset_api.dataset.schema.Mutation, dataset_api.organization_schema.Mutation,
               dataset_api.catalog_schema.Mutation,
               dataset_api.resource_schema.Mutation, dataset_api.tag_schema.Mutation,
               dataset_api.geography_schema.Mutation,
               dataset_api.api_source_schema.Mutation, dataset_api.rating_schema.Mutation,
               dataset_api.license.license_schema.Mutation, dataset_api.dataset_access_model_request.schema.Mutation,
               dataset_api.sector_schema.Mutation, dataset_api.additional_info_schema.Mutation,
               dataset_api.data_request.schema.Mutation, dataset_api.organization_request_schema.Mutation,
               dataset_api.data_access_model.schema.Mutation, dataset_api.dataset_moderation.Mutation,
               dataset_api.dataset_access_model_resource.schema.Mutation, dataset_api.aggrements.schema.Mutation,
               dataset_api.license_addition.license_addition_schema.Mutation,
               graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
