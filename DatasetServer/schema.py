import graphene
import dataset_api.dataset_schema
import dataset_api.organization_schema
import dataset_api.catalog_schema
import dataset_api.resource_schema
import dataset_api.tag_schema
import dataset_api.geography_schema
import dataset_api.api_source_schema
import dataset_api.api_resource_schema
import dataset_api.rating_schema


class Query(dataset_api.dataset_schema.Query, dataset_api.organization_schema.Query, dataset_api.catalog_schema.Query,
            dataset_api.resource_schema.Query, dataset_api.tag_schema.Query, dataset_api.geography_schema.Query,
            dataset_api.api_source_schema.Query,dataset_api.api_resource_schema.Query,dataset_api.rating_schema.Query,
            graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_dataset = dataset_api.dataset_schema.CreateDataset.Field()
    update_dataset = dataset_api.dataset_schema.UpdateDataset.Field()
    create_resource = dataset_api.resource_schema.CreateResource.Field()
    update_resource = dataset_api.resource_schema.UpdateResource.Field()
    delete_resource = dataset_api.resource_schema.DeleteResource.Field()
    create_catalog = dataset_api.catalog_schema.CreateCatalog.Field()
    create_tag = dataset_api.tag_schema.CreateTag.Field()
    create_geography = dataset_api.geography_schema.CreateGeography.Field()
    create_api_source = dataset_api.api_source_schema.CreateAPISource.Field()
    create_api_resource = dataset_api.api_resource_schema.CreateAPIResource.Field()
    update_api_resource = dataset_api.api_resource_schema.UpdateAPIResource.Field()
    delete_api_resource = dataset_api.api_resource_schema.DeleteAPIResource.Field()
    create_dataset_rating = dataset_api.rating_schema.CreateDatasetRating.Field()
    create_organization = dataset_api.organization_schema.CreateOrganization.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
