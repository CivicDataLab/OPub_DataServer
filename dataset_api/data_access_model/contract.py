import os
from typing import List

import pdfkit
from django.core.files.base import ContentFile

from dataset_api.data_access_model.models import DataAccessModel
from dataset_api.license.models import License, LicenseAddition


def create_contract(model_license: License, additions: List, data_access_model: DataAccessModel):
    if not additions:
        return
    text = model_license.title
    text = text + model_license.description
    for addition_id in additions:
        addition = LicenseAddition.objects.get(id=addition_id)
        text = text + addition.title
        text = text + addition.description
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': 'UTF-8',
        'quiet': ''
    }
    pdfkit.from_string(text, 'out.pdf', options=options)

    with open("out.pdf", 'rb') as f:
        rawdata = f.read()
        data_access_model.contract.save('contract.pdf', ContentFile(rawdata))

    os.remove("./out.pdf")
