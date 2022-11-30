import datetime
import os
from typing import Iterable

import pdfkit
from django.core.files.base import ContentFile

from dataset_api.models import DatasetAccessModel, Agreement, Dataset
from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.License import License
from dataset_api.models.LicenseAddition import LicenseAddition

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
        additions = []
    text = extract_text(additions, model_license, data_access_model)

    pdfkit.from_string(text, 'out.pdf', options=pdf_options)

    with open("out.pdf", 'rb') as f:
        rawdata = f.read()
        data_access_model.contract.save('contract.pdf', ContentFile(rawdata))

    os.remove("./out.pdf")


def extract_text(additions, model_license, data_access_model: DataAccessModel):
    text = ""
    for addition in additions:
        addition = LicenseAddition.objects.get(id=addition)
        text = text + addition.title
        text = text + addition.description
    dam_license_content = body = f"""
    <html>
      <head>
        <meta name="pdfkit-page-size" content="Legal"/>
        <meta name="pdfkit-orientation" content="Portrait"/>
      </head>
      <h1>Agreement</h1>
      <h2>{model_license.title} </h2>
      <p>This document acts as license condition set for the Data Access Model {data_access_model.title} <p>
      <br/>
      <p>{model_license.description} </p>
      <h2>Additional Terms and Conditions </h2>
      <p>{text}<p>
      </html>
    """
    return dam_license_content


def get_agreement_resource_details(dataset_access_model: DatasetAccessModel):
    text = """<ol>"""
    for resource in dataset_access_model.datasetaccessmodelresource_set.all():
        text = text + f"""
          <li>
            {resource.resource.title}, last updated on {resource.resource.modified}: """
        if not resource.fields.exists():
            text = text + """All data columns/fields"""
        else:
            for field in resource.fields.all():
                text = text + f""" [{field.key} ({field.id})]"""
        text = text + """</li>"""
    text = text + """</ol>"""
    return text


def get_dataset_resource_details(dataset: Dataset):
    text = """<ol>"""
    for resource in dataset.resource_set.all():
        text = text + f"""
          <li>
            {resource.title}, last updated on {resource.modified}: """
        text = text + """</li>"""
    text = text + """</ol>"""
    return text


def get_additional_conditions_text(dataset_access_model: DatasetAccessModel):
    additional_conditions = dataset_access_model.data_access_model.license_additions.all()
    text = ""
    if additional_conditions and len(additional_conditions) > 0:
        text = text + """<li style="font-weight: bold">Additional terms and conditions:</li><ol type="1">"""
        for condition in additional_conditions:
            text = text + f""" <li>{condition.title}: {condition.description}</li> """
        text = text + "/<ol>"
    return text


def extract_agreement_text(dataset_access_model: DatasetAccessModel, username, agreement_model: Agreement):
    organization = dataset_access_model.data_access_model.organization

    text = f"""
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Data Access Agreement</title>
        <style>
        .document{{
            background-color: rgb(255, 255, 255);
            border: 1px solid black;
            margin: auto;
            padding: 2rem;
            width: 1216px;
        }}
        
        .header{{
            display: flex;
            justify-content: space-between;
        }}
        
        .content p{{
        
            line-height: 1.4;
        
        }}
        
        ol{{
            margin: 10px 0;
        }}
        .footer{{
            display: flex;
            justify-content: space-between;
        }}

        </style>
      </head>
      <body>
        <div class="document">
          <div class="header">
            <img src="" alt="[Logo of Data Provider]" />
            <img src="" alt="[Logo of IDP]" />
          </div>
          <div style="text-align: center">
            <h2>Data Access Agreement ({agreement_model.id})</h2>
          </div>
          <div class="content">
            <p>
              This DATA ACCESS AGREEMENT (hereinafter the “Agreement”), effective as of {datetime.datetime.now()}, is entered into by and between
              <a href="{organization.homepage}">{organization.title}</a>, a State Government entity,(hereinafter the “Data Provider”),
              and {username}</a> (hereinafter the “Data Consumer”).
            </p>
            <p>
              Whereas, Data Provider has collected/compiled/generated and/or controls/manages the data resources specified in section 1 (hereinafter the
              “Data”),
            </p>
    
            <p>
              Whereas, Data Provider has shared the Data via India Data Platform (hereinafter the “IDP”) and made it available for users of IDP to
              discover, access and use as per the access type, data access model, licence and additional terms and conditions (if any) specified by the
              Data Provider in section 2,
            </p>
            <p>
              Whereas, Data Provider agrees to share the Data via IDP in agreement with the terms and conditions for the Data Provider specified in
              section 3 in particular and all sections of this Agreement in general, and
            </p>
            <p>
              Whereas, Data Consumer agrees to access and use the Data shared via IDP in agreement with the terms and conditions for the Data Consumer
              specified in section 4 in particular and all sections of this Agreement in general,
            </p>
            <p>
              In consideration of the above premises, and of the details of Data and mutual promises herein contained, the parties do hereby agree as
              follows:
            </p>
            <ol>
              <li style="font-weight: bold">Data</li>
              <p>
                The Data shared by the Data Provider with the Data Consumer through this Agreement signed on [Date] includes the following columns/fields
                of the below mentioned data resources and supporting documents (if any).
              </p>
              <ol type="a" class="childlisting">
                <li style="font-weight: bold">Resources</li>
                {get_agreement_resource_details(dataset_access_model)}
    
              <li style="font-weight: bold">Data Access Model</li>
              <p>
                The Data, that is the set of data resources and supporting documents (if any) mentioned in section 1, is being shared by the Data Provider
                with the Data Consumer under the access type, licence and additional terms and conditions (if any) specified by the following data access
                model:
              </p>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px"><b>Name of data access model:</b>&nbsp;<span>{dataset_access_model.data_access_model.title}</span></li>
    
                <li style="margin-bottom: 10px"><b>Access type:</b>&nbsp;<span>{dataset_access_model.data_access_model.type}</span></li>
                <li style="margin-bottom: 10px">
                  <b>Licence:</b><span>&nbsp;{dataset_access_model.data_access_model.license.title}</span>
                </li>
                {get_additional_conditions_text(dataset_access_model)}
                
    
              <li style="font-weight: bold">Terms and Conditions for the Data Consumer</li>
              <p style="font-weight: bold">{dataset_access_model.data_access_model.license.title}</p>
                <p> {dataset_access_model.data_access_model.license.description} </p>
              <li style="font-weight: bold">Termination</li>
              <p>
                [Add]
                <br />
                [Take Down Notice]
              </p>
    
              <li style="font-weight: bold">Dispute Redressal Mechanism</li>
              <p>[Add]</p>
              <li style="font-weight: bold">Governing Law</li>
              <p>This Agreement is governed by Indian law.</p>
            </ol>
            <p style="text-align: center">***</p>
            <p>
              Data Provider and Data Consumer agree and acknowledge that this Agreement represents the entire agreement between. In the event that Data
              Provider and Data Consumer desire to change, add, or otherwise modify any terms contained in this Agreement, the same shall be done through
              mutual communication, agreement and re-accessing the Data concerned via IDP.
            </p>
            <p>This Agreement is duly executed by the duly authorised representatives of the parties as below:</p>
          </div>
          <div class="footer">
            <div>
              <p>On behalf of {organization.title}</p>
              <p>[Box for digital signature - Implement later]</p>
              <p>First Name & Last Name of Authorised Signatory]</p>
              <p>Name of Authorised Signatory]</p>
              <p{organization.contact_email}</p>
              <p>{datetime.datetime.now()}</p>
            </div>
            <div>
              <p>On behalf of India Data Platform</p>
              <p>[Box for digital signature - Implement later]</p>
              <p>[First Name & Last Name of Authorised Signatory]</p>
              <p>[E-mail address]</p>
              <p>{datetime.datetime.now()}</p>
            </div>
          </div>
          <p>India Data Platform – Data Access Agreement – {agreement_model.id}</p>
        </div>
      </body>
    </html>

    """
    return text


def create_consumer_agreement(dataset_access_model: DatasetAccessModel, username, agreement_model: Agreement):
    if not username:
        username = "Anonymous User"
    data_access_model = dataset_access_model.data_access_model
    additions = data_access_model.license_additions.all()
    model_license = data_access_model.license
    text = extract_agreement_text(dataset_access_model, username, agreement_model)

    # text = text + extract_text(additions, model_license, data_access_model)

    pdfkit.from_string(text, 'out.pdf', options=pdf_options)

    with open("out.pdf", 'rb') as f:
        rawdata = f.read()
        agreement_model.accepted_agreement.save('agreement.pdf', ContentFile(rawdata))

    os.remove("./out.pdf")


def extract_provider_agreement(dataset: Dataset, username):
    organization = dataset.catalog.organization

    text = f"""
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Data Sharing Agreement {organization.id}-{dataset.id}</title>
        <style>
        .document{{
            background-color: rgb(255, 255, 255);
            border: 1px solid black;
            margin: auto;
            padding: 2rem;
            width: 1216px;
        }}
        
        .header{{
            display: flex;
            justify-content: space-between;
        }}
        
        .content p{{
        
            line-height: 1.4;
        
        }}
        
        ol{{
            margin: 10px 0;
        }}
        .footer{{
            display: flex;
            justify-content: space-between;
        }}

        </style>
      </head>
      <body>
        <div class="document">
          <div class="header">
            <img src="" alt="[Logo of Data Provider]" />
            <img src="" alt="[Logo of IDP]" />
          </div>
          <div style="text-align: center">
            <h2>Data Sharing Agreement {organization.id}-{dataset.id}</h2>
          </div>
          <div class="content">
            <p>
              This DATA SHARING AGREEMENT (hereinafter the “Agreement”), effective as of {datetime.datetime.now()}, is entered into by and between
              <a href="{organization.homepage}">{organization.title}</a>, a State Government entity,(hereinafter the “Data Provider”),
              and <a href="https://idp.civicdatalab.in/">India Data Platform</a> (hereinafter the “IDP”) managed by National Informatics Centre, with its
                main office located in A-Block, Lodhi Road, CGO Complex, New Delhi, 110003.
            </p>
            <p>
              Whereas, Data Provider has collected/compiled/generated and/or controls/manages the data resources specified in section 1 (hereinafter the
              “Data”),
            </p>
    
            <p>
              Whereas, Data Provider wishes to share the Data via IDP and to make it available for users of IDP to discover, access and use as per the
              access type(s), data access model(s), licence(s) and additional terms and conditions (if any) to be specified by the Data Provider,
            </p>
            <p>
              Whereas, Data Provider agrees to share the Data via IDP in agreement with the terms and conditions for the Data Provider specified in
              section 2 in particular and with all sections of this Agreement in general, and
            </p>
            <p>
              Whereas, IDP agrees to make the Data available on IDP in agreement with the terms and conditions for the IDP specified in section 3 in
              particular and with all sections of this Agreement in general,
            </p>
            <p>
              In consideration of the above premises, and of the details of Data and mutual promises herein contained, the parties do hereby agree as
              follows:
            </p>
            <ol>
              <li style="font-weight: bold">Data</li>
              <p>
                The Data shared by the Data Provider with the Data Consumer through this Agreement signed on [Date] includes the following columns/fields
                of the below mentioned data resources and supporting documents (if any).
              </p>
              <ol type="a" class="childlisting">
                <li style="font-weight: bold">Resources</li>
                {get_dataset_resource_details(dataset)}
    
                <li style="font-weight: bold">Terms and Conditions for the Data Provider</li>
                  <p>[Add]</p>
        
                <li style="font-weight: bold">Terms and Conditions for the India Data Platform</li>
                  <p>[Add]</p>
    
              <li style="font-weight: bold">Termination</li>
              <p>
                [Add]
                <br />
                [Take Down Notice]
              </p>
    
              <li style="font-weight: bold">Dispute Redressal Mechanism</li>
              <p>[Add]</p>
              <li style="font-weight: bold">Governing Law</li>
              <p>This Agreement is governed by Indian law.</p>
            </ol>
            <p style="text-align: center">***</p>
            <p>
              Data Provider and IDP agree and acknowledge that this Agreement represents the entire agreement between. In the event that the Data Provider
              and IDP desire to change, add or otherwise modify any terms contained in this Agreement, the same shall be done through mutual
              communication, agreement and re-sharing of the Data concerned via IDP. This Agreement is duly executed by the duly authorised
              representatives of the parties as below:
            </p>
            <p><p>This Agreement is duly executed by the duly authorised representatives of the parties as below:</p>
          </div>
          <div class="footer">
            <div>
              <p>On behalf of {organization.title}</p>
              <p>[Box for digital signature - Implement later]</p>
              <p>First Name & Last Name of Authorised Signatory]</p>
              <p>Name of Authorised Signatory]</p>
              <p{organization.contact_email}</p>
              <p>{datetime.datetime.now()}</p>
            </div>
            <div>
              <p>On behalf of India Data Platform</p>
              <p>[Box for digital signature - Implement later]</p>
              <p>[First Name & Last Name of Authorised Signatory]</p>
              <p>[E-mail address]</p>
              <p>{datetime.datetime.now()}</p>
            </div>
          </div>
          <p>India Data Platform – Data Sharing Agreement {organization.id}-{dataset.id}</p>
        </div>
      </body>
    </html>

    """
    return text


def update_provider_agreement(dataset: Dataset, username):
    text = extract_provider_agreement(dataset, username)

    pdfkit.from_string(text, 'out.pdf', options=pdf_options)

    with open("out.pdf", 'rb') as f:
        rawdata = f.read()
        dataset.accepted_agreement.save('agreement.pdf', ContentFile(rawdata))

    os.remove("./out.pdf")
