import os


def _organization_directory_path(org, filename):
    """
    Create a directory path to upload the organization logo

    """

    org_name = org.title
    _, extension = os.path.splitext(filename)
    return f"public/organizations/{org_name}/{extension[1:]}/{filename}"


def _organization_file_directory_path(org, filename):
    """
    Create a directory path to upload the sample data file.

    """

    org_name = org.title
    _, extension = os.path.splitext(filename)
    return f"resources/{org_name}/sample_data/{extension[1:]}/{filename}"


def _resource_directory_path(file_details, filename):
    """
    Create a directory path to upload the resources.

    """
    dataset_name = file_details.resource.dataset.title
    resource_name = file_details.resource.title
    _, extension = os.path.splitext(filename)
    return f"resources/{dataset_name}/{resource_name}/{extension[1:]}/{filename}"


def _info_directory_path(info, filename):
    """
    Create a directory path to upload additional info.

    """
    dataset_name = info.dataset.title
    resource_name = info.title
    _, extension = os.path.splitext(filename)
    return f"info/{dataset_name}/{resource_name}/{extension[1:]}/{filename}"


def _contract_directory_path(dam, filename):
    """
    Create a directory path to upload DAM contract files.

    """
    org_name = dam.organization.title
    dam_name = dam.title
    _, extension = os.path.splitext(filename)
    return f"info/{org_name}/{dam_name}/{extension[1:]}/{filename}"


def _license_directory_path(license, filename):
    """
    Create a directory path to upload license files.

    """
    license_name = license.title
    _, extension = os.path.splitext(filename)
    return f"info/{license_name}/{extension[1:]}/{filename}"


def _data_request_directory_path(request, filename):
    """
    Create a directory path to receive the request data.

    """
    _, extension = os.path.splitext(filename)
    return f"request/{request.id}/{extension[1:]}/{filename}"


def _agreement_directory_path(agreement, filename):
    """
    Create a directory path to receive the request data.

    """
    _, extension = os.path.splitext(filename)
    return f"request/{agreement.id}/{extension[1:]}/{filename}"
