import graphene
import dataset_api.dataset_schema
import dataset_api.organization_schema
import dataset_api.catalog_schema
import dataset_api.resource_schema
import dataset_api.tag_schema
import dataset_api.geography_schema
import dataset_api.sector_schema
import dataset_api.api_source_schema
import dataset_api.api_resource_schema
import dataset_api.additional_info_schema
import dataset_api.rating_schema
import dataset_api.fetch_dataset
import dataset_api.data_access_model_schema
import dataset_api.dataset_moderation
import dataset_api.data_access_model_request_schema


class Query(dataset_api.dataset_schema.Query, dataset_api.organization_schema.Query, dataset_api.catalog_schema.Query,
            dataset_api.resource_schema.Query, dataset_api.tag_schema.Query, dataset_api.geography_schema.Query,
            dataset_api.api_source_schema.Query, dataset_api.api_resource_schema.Query, dataset_api.rating_schema.Query,
            dataset_api.sector_schema.Query, dataset_api.additional_info_schema.Query, dataset_api.fetch_dataset.Query,
            dataset_api.data_access_model_schema.Query, dataset_api.dataset_moderation.Query,
            dataset_api.data_access_model_request_schema.Query, graphene.ObjectType):
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
    create_sector = dataset_api.sector_schema.CreateSector.Field()
    create_api_source = dataset_api.api_source_schema.CreateAPISource.Field()
    # create_api_resource = dataset_api.api_resource_schema.CreateAPIResource.Field()
    # update_api_resource = dataset_api.api_resource_schema.UpdateAPIResource.Field()
    # delete_api_resource = dataset_api.api_resource_schema.DeleteAPIResource.Field()
    create_additional_info = dataset_api.additional_info_schema.CreateAdditionInfo.Field()
    update_additional_info = dataset_api.additional_info_schema.UpdateAdditionalInfo.Field()
    delete_additional_info = dataset_api.additional_info_schema.DeleteAdditionalInfo.Field()
    create_dataset_rating = dataset_api.rating_schema.CreateDatasetRating.Field()
    create_organization = dataset_api.organization_schema.CreateOrganization.Field()
    data_request = dataset_api.fetch_dataset.DataRequestMutation.Field()
    update_data_request = dataset_api.fetch_dataset.DataRequestUpdateMutation.Field()
    approve_reject_data_request = dataset_api.fetch_dataset.ApproveRejectDataRequest.Field()
    moderation_request = dataset_api.dataset_moderation.ModerationRequestMutation.Field()
    approve_reject_moderation_request = dataset_api.dataset_moderation.ApproveRejectModerationRequest.Field()
    data_access_model_request = dataset_api.data_access_model_request_schema.DataAccessModelRequestMutation.Field()
    approve_reject_data_access_model_request = dataset_api.data_access_model_request_schema.ApproveRejectDataAccessModelRequest.Field()
    create_data_access_model = dataset_api.data_access_model_schema.CreateDataAccessModel.Field()
    patch_dataset = dataset_api.dataset_schema.PatchDataset.Field()
    access_model_resource = dataset_api.data_access_model_schema.CreateAccessModelResource.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
