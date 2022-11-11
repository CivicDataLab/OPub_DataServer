from typing import Iterable

import graphene
from graphql_auth.bases import Output

from dataset_api.decorators import auth_user_by_org
from dataset_api.license.decorators import check_license_role
from dataset_api.license_addition.enums import LicenseAdditionStatus
from dataset_api.models import LicenseAddition, License


class LicenceAdditionType(graphene.InputObjectType):
    id = graphene.ID(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    generic_item = graphene.Boolean(required=True)


class LicenseAdditionsCreateInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    generic_item = graphene.Boolean(required=True)
    license = graphene.ID(required=True)


class LicenseAdditionApproveRejectInput(graphene.InputObjectType):
    ids: Iterable = graphene.List(graphene.ID, required=True)
    reject_reason = graphene.String(required=False)
    status = graphene.Enum.from_enum(LicenseAdditionStatus)(required=True)


def _create_license_addition(license_instance, addition: LicenceAdditionType):
    addition_instance = LicenseAddition(
        license=license_instance,
        description=addition.description,
        title=addition.title,
        generic_item=addition.generic_item,
    )
    addition_instance.save()


def _create_update_license_additions(
        license_instance: License, additions: [LicenceAdditionType]
):
    license_additions_ids = []  # List of schemas that already exists.
    license_addition_instances = LicenseAddition.objects.filter(
        license=license_instance
    )
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
                license_additions_ids.remove(
                    int(license_addition_instance.id)
                )  # Remove id from the list
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


class CreateLicenseAddition(graphene.Mutation, Output):
    class Arguments:
        license_addition_data = LicenseAdditionsCreateInput(required=True)

    license = graphene.Field(LicenceAdditionType)

    @staticmethod
    @check_license_role
    def mutate(root, info, role, addition_data: LicenseAdditionsCreateInput = None):
        license_instance = License.objects.get(id=addition_data.license)
        addition_instance = LicenseAddition(title=addition_data.title, description=addition_data.description,
                                            license=license_instance)
        if role == "DPA":
            addition_instance.status = LicenseAdditionStatus.CREATED.value
            addition_instance.generic_item = False
        if role == "PMU":
            addition_instance.status = LicenseAdditionStatus.PUBLISHED.value
            addition_instance.generic_item = addition_data.generic_item
        addition_instance.save()
        return CreateLicenseAddition(license=addition_instance)


class UpdateLicenseAddition(graphene.Mutation, Output):
    class Arguments:
        license_addition_data = LicenseAdditionsCreateInput(required=True)

    license = graphene.Field(LicenceAdditionType)

    @staticmethod
    @check_license_role
    def mutate(root, info, role, addition_data: LicenseAdditionsCreateInput = None):
        license_instance = License.objects.get(id=addition_data.license)
        addition_instance = LicenseAddition.objects.get(id=addition_data.id)
        addition_instance.license = license_instance
        addition_instance.title = addition_data.title
        addition_instance.description = addition_data.description
        if role == "DPA":
            addition_instance.status = LicenseAdditionStatus.CREATED.value
            addition_instance.generic_item = False
        if role == "PMU":
            addition_instance.status = LicenseAdditionStatus.PUBLISHED.value
            addition_instance.generic_item = addition_data.generic_item
        addition_instance.save()
        return UpdateLicenseAddition(license=addition_instance)


class ApproveRejectLicenseAddition(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseAdditionApproveRejectInput(required=True)

    license_requests = graphene.List(LicenceAdditionType)

    @staticmethod
    @auth_user_by_org(action="approve_license")
    def mutate(root, info, additions_data: LicenseAdditionApproveRejectInput = None):
        errors = []
        additions_requests = []
        for license_id in additions_data.ids:
            try:
                additions_instance = LicenseAddition.objects.get(id=license_id)
            except License.DoesNotExist as e:
                return errors.append(
                    {"message": "License addition with given id not found", "code": "404"}
                )

            additions_instance.status = additions_data.status
            if additions_data.reject_reason:
                additions_instance.reject_reason = additions_data.reject_reason
            additions_instance.save()
            additions_requests.append(additions_instance)
        if errors:
            return {"success": False, "errors": {"ids": errors}}

        return ApproveRejectLicenseAddition(license_requests=additions_requests)


class Mutation(graphene.ObjectType):
    create_license_addition = CreateLicenseAddition.Field()
    update_license_addition = UpdateLicenseAddition.Field()
    approve_reject_license_addition = ApproveRejectLicenseAddition.Field()
