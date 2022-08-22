import graphene
import dataset_api.dataset_schema
import dataset_api.catalog_schema
import dataset_api.resource_schema


class Query(dataset_api.dataset_schema.Query,
            graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_dataset = dataset_api.dataset_schema.CreateDataset.Field()
    create_resource = dataset_api.resource_schema.CreateResource.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
