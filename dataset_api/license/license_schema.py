import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from dataset_api.enums import LicenseStatus
from dataset_api.models import Organization
from dataset_api.license.models import License, LicenseAddition
from dataset_api.decorators import check_license_role


class LicenseAdditionType(DjangoObjectType):
    class Meta:
        model = LicenseAddition
        fields = "__all__"


class LicenseType(DjangoObjectType):
    additions = graphene.List(LicenseAdditionType)

    class Meta:
        model = License
        fields = "__all__"

    def resolve_additions(self, info):
        try:
            return LicenseAddition.objects.filter(Q(license=self) | Q(generic_item=True))
        except LicenseAddition.DoesNotExist as e:
            return []


class Query(graphene.ObjectType):
    all_license = graphene.List(LicenseType)
    license = graphene.Field(LicenseType, license_id=graphene.Int())

    def resolve_all_license(self, info, **kwargs):
        return License.objects.all().order_by("-modified")

    def resolve_license(self, info, license_id):
        return License.objects.get(pk=license_id)


class LicenseApproveRejectInput(graphene.InputObjectType):
    ids = graphene.List(graphene.ID, required=True)
    reject_reason = graphene.String(required=False)
    # TODO: Re-visit duplicate license status
    status = graphene.String(required=True)
    # status = graphene.Enum.from_enum(LicenseStatus)(required=True)


class LicenceAdditionsInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    generic_item = graphene.Boolean(required=True)


class LicenseInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    organization = graphene.ID(required=True)
    file = Upload(required=False)
    remote_url = graphene.String(required=False)
    license_additions = graphene.List(LicenceAdditionsInput, required=False, default=[])


def _create_license_addition(license_instance, addition: LicenceAdditionsInput):
    addition_instance = LicenseAddition(
        license=license_instance,
        description=addition.description,
        title=addition.title,
        generic_item=addition.generic_item
    )
    addition_instance.save()


def _create_update_license_additions(license_instance: License, additions: [LicenceAdditionsInput]):
    license_additions_ids = []  # List of schemas that already exists.
    license_addition_instances = LicenseAddition.objects.filter(license=license_instance)
    for license_addition in license_addition_instances:
        license_additions_ids.append(license_addition.id)

    for addition in additions:
        try:
            # Update existing addition
            if addition.id:
                license_addition_instance = LicenseAddition.objects.get(id=addition.id)
                license_addition_instance.title = addition.title
                license_addition_instance.description = addition.description
                license_addition_instance.license = license_instance
                license_addition_instance.generic_item = addition.generic_item
                license_addition_instance.save()
                license_additions_ids.remove(int(license_addition_instance.id))  # Remove id from the list
            else:
                # Add new addition
                _create_license_addition(license_instance, addition)
        except LicenseAddition.DoesNotExist as e:
            _create_license_addition(license_instance, addition)
    # Delete addition which were not updated or created.
    if license_additions_ids:
        for ids in license_additions_ids:
            license_addition = LicenseAddition.objects.get(id=ids)
            license_addition.delete()


class CreateLicense(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseInput(required=True)

    license = graphene.Field(LicenseType)

    @staticmethod
    @check_license_role
    def mutate(root, info, role, license_data: LicenseInput = None):
        organization = Organization.objects.get(id=license_data.organization)
        license_instance = License(
            title=license_data.title,
            description=license_data.description,
            created_organization=organization,
        )
        if license_data.file:
            license_instance.file = license_data.file
        if license_data.remote_url:
            license_instance.remote_url = license_data.remote_url
        if role == "DPA":
            license_instance.status = LicenseStatus.CREATED.value
        if role == "PMU":
            license_instance.status = LicenseStatus.PUBLISHED.value
        license_instance.save()
        if license_data.license_additions:
            _create_update_license_additions(license_instance, license_data.license_additions)
        return CreateLicense(license=license_instance)


class UpdateLicense(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseInput(required=True)

    license = graphene.Field(LicenseType)

    @staticmethod
    @check_license_role
    def mutate(root, info, role, license_data: LicenseInput = None):
        try:
            organization = Organization.objects.get(id=license_data.organization)
            license_instance = License.objects.get(id=license_data.id)
        except (License.DoesNotExist, Organization.DoesNotExist) as e:
            return {"success": False,
                    "errors": {
                        "id": [{"message": "License or organization with given id not found", "code": "404"}]}}

        license_instance.title = license_data.title
        license_instance.description = license_data.description
        license_instance.created_organization = organization
        if license_data.file:
            license_instance.file = license_data.file
        if license_data.remote_url:
            license_instance.remote_url = license_data.remote_url
        if role == "DPA":
            license_instance.status = LicenseStatus.CREATED.value
        if role == "PMU":
            license_instance.status = LicenseStatus.PUBLISHED.value
        license_instance.save()
        if license_data.license_additions:
            _create_update_license_additions(license_instance, license_data.license_additions)
        return CreateLicense(license=license_instance)


class ApproveRejectLicense(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseApproveRejectInput(required=True)

    license_requests = graphene.List(LicenseType)

    @staticmethod
    def mutate(root, info, license_data: LicenseApproveRejectInput = None):
        errors = []
        license_requests = []
        for license_id in license_data.ids:
            try:
                license_instance = License.objects.get(id=license_id)
            except License.DoesNotExist as e:
                return errors.append({"message": "License with given id not found", "code": "404"})

            license_instance.status = license_data.status
            if license_data.reject_reason:
                license_instance.reject_reason = license_data.reject_reason
            license_instance.save()
            license_requests.append(license_instance)
        if errors:
            return {"success": False,
                    "errors": {
                        "ids": errors}}

        return ApproveRejectLicense(license_requests=license_requests)


class DeleteLicense(graphene.Mutation, Output):
    class Arguments:
        license_id = graphene.ID(required=True)

    success = graphene.String()

    # resource = graphene.Field(ResourceType)

    @staticmethod
    @check_license_role
    def mutate(root, info, license_id: graphene.ID):
        license_instance = License.objects.get(id=license_id)
        license_instance.delete()
        return DeleteLicense(success=True)


class Mutation(graphene.ObjectType):
    create_license = CreateLicense.Field()
    update_license = UpdateLicense.Field()
    approve_reject_license = ApproveRejectLicense.Field()
    delete_license = DeleteLicense.Field()
