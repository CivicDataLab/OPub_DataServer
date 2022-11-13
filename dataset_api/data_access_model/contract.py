import os
from typing import List, Iterable

import pdfkit
from django.core.files.base import ContentFile

from dataset_api.models import DatasetAccessModel, Agreement
from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.LicenseAddition import LicenseAddition
from dataset_api.models.License import License

pdf_options = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': 'UTF-8',
    'quiet': ''
}


def create_contract(model_license: License, additions: Iterable, data_access_model: DataAccessModel):
    if not additions:
        return
    text = extract_text(additions, model_license, data_access_model)

    pdfkit.from_string(text, 'out.pdf', options=pdf_options)

    with open("out.pdf", 'rb') as f:
        rawdata = f.read()
        data_access_model.contract.save('contract.pdf', ContentFile(rawdata))

    os.remove("./out.pdf")


def extract_text(additions, model_license, data_access_model: DataAccessModel):
    text = ""
    for addition in additions:
        # addition = LicenseAddition.objects.get(id=addition)
        text = text + addition.title
        text = text + addition.description
    dam_license_content = body = f"""
    <html>
      <head>
        <meta name="pdfkit-page-size" content="Legal"/>
        <meta name="pdfkit-orientation" content="Portrait"/>
      </head>
      <h1>Agreeement</h1>
      <h2>{model_license.title} </h2>
      <p>This document acts as license condition set for the Data Access Model {data_access_model.title} <p>
      <br/>
      <p>{model_license.description} </p>
      <h2>Additional Conditions </h2>
      <p>{text}<p>
      </html>
    """
    return dam_license_content


def create_agreement(dataset_access_model: DatasetAccessModel, username, agreement_model: Agreement):
    if not username:
        username = "Anonymous User"
    data_access_model = dataset_access_model.data_access_model
    additions = data_access_model.license_additions.all()
    model_license = data_access_model.license
    text = f"This is agreement between{username} and {data_access_model.organization.title} for dataset " \
           f"{dataset_access_model.dataset.title} "

    text = text + extract_text(additions, model_license, data_access_model)

    pdfkit.from_string(text, 'out.pdf', options=pdf_options)

    with open("out.pdf", 'rb') as f:
        rawdata = f.read()
        agreement_model.accepted_agreement.save('agreement.pdf', ContentFile(rawdata))

    os.remove("./out.pdf")
