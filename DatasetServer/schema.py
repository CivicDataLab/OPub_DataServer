import graphene
import dataset_api.dataset_schema
import dataset_api.organization_schema
import dataset_api.catalog_schema
import dataset_api.resource_schema


class Query(dataset_api.dataset_schema.Query, dataset_api.organization_schema.Query, dataset_api.catalog_schema.Query,
            dataset_api.resource_schema.Query,
            graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_dataset = dataset_api.dataset_schema.CreateDataset.Field()
    update_dataset = dataset_api.dataset_schema.UpdateDataset.Field()
    create_resource = dataset_api.resource_schema.CreateResource.Field()
    create_catalog = dataset_api.catalog_schema.CreateCatalog.Field()
    create_organization = dataset_api.organization_schema.CreateOrganization.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
