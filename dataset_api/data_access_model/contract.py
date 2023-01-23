import datetime
import os
from typing import Iterable

import pdfkit
from django.core.files.base import ContentFile

from DatasetServer import settings
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
          <li style="margin-bottom: 10px">
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
          <li style="margin-bottom: 10px">
            {resource.title}, last updated on {resource.modified}: """
        text = text + """</li>"""
    text = text + """</ol>"""
    return text


def get_additional_conditions_text(dataset_access_model: DatasetAccessModel):
    additional_conditions = dataset_access_model.data_access_model.license_additions.all()
    text = ""
    if additional_conditions and len(additional_conditions) > 0:
        text = text + """<li style="font-weight: bold">Additional terms and conditions:</li>
        <ol type="1">"""
        for condition in additional_conditions:
            text = text + f""" <li style="margin-bottom: 10px">{condition.title}: {condition.description}</li> """
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
        body span {{
            line-height: 1.4;    
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
              <a href="{organization.homepage}">{organization.title}</a>, a {organization.organization_types} (hereinafter the “Data
              Provider”), and {username}, Individual (hereinafter the “Data Consumer”).
            </p>
            <p>
              Whereas, Data Provider has collected/compiled/generated/harvested and/or controls/manages the data distributions specified in section 1.
              Data (hereinafter the “Data”),
            </p>
    
            <p>
              Whereas, Data Provider has shared the Data via India Data Platform (hereinafter the “IDP”) and made it available for users of IDP to
              discover, access and use as per the access type, data access model, licence and additional terms and conditions (if any) specified by the
              Data Provider in section 2. Data Access Model,
            </p>
            <p>
              Whereas, Data Provider agrees to share the Data via IDP in agreement with the terms and conditions for the Data Provider specified in
              section 3. Terms and Conditions for the Data Provider in particular and all sections of this Agreement in general, and
            </p>
            <p>
              Whereas, Data Consumer agrees to access and use the Data shared via IDP in agreement with the terms and conditions for the Data Consumer
              specified in section 4. Terms and Conditions for the Data Consumer in particular and all sections of this Agreement in general,
            </p>
            <p>
              In consideration of the above premises, and of the details of Data and mutual promises herein contained, the parties do hereby agree as
              follows:
            </p>
            <ol>
              <li style="font-weight: bold">Data</li>
              <p>
                The Data shared by the Data Provider with the Data Consumer through this Agreement signed on Date includes the following columns/fields of
                the below mentioned data distributions.
              </p>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px"><b>Distributions (Data/APIs)</b></li>
                {get_agreement_resource_details(dataset_access_model)}
    
              <li style="font-weight: bold">Data Access Model</li>
              <p>
                The Data, that is the set of data distributions mentioned in section 1. Data of this Agreement, is being shared by the Data Provider with
                the Data Consumer under the following data access model:
              </p>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px"><b>Name of data access model:</b>&nbsp;<span>{dataset_access_model.data_access_model.title}</span></li>
    
                <li style="margin-bottom: 10px"><b>Type of Access:</b>&nbsp;<span>{dataset_access_model.data_access_model.type}</span></li>
                <li style="margin-bottom: 10px">
                  <b>Policy:</b>&nbsp;<span
                     NA;
                  </span>
                </li>
                
                <li style="margin-bottom: 10px">
                  <b>Licence:</b><span>&nbsp;{dataset_access_model.data_access_model.license.title}</span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Licence Fees:</b>&nbsp;<span>
                    None;
                  </span>
                </li>
                {get_additional_conditions_text(dataset_access_model)}
              
              <li style="font-weight: bold">Terms and Conditions for the Data Provider</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">
                  <b>Lawful Provision of Data:</b>
                  &nbsp;<span
                    >The Data Provider declares that the Data concerned (as detailed in section 1. Data of this Agreement), which has been made available
                    via IDP by the Data Provider and access to which is being provided to the Data Consumer via this Agreement, has been lawfully
                    collected/compiled/generated by the Data Provider and/or the Data Provider has the legal authority to control/manage/share the Data
                    Concerned under the data access model specified by the Data Provider.</span
                  >
                </li>
                <li style="margin-bottom: 10px">
                  <b>Comprehensiveness of the Agreement:</b>
                  &nbsp;<span>
                    The Data Provider declares that the data access model (including but not limited to access type, licence and additional terms and
                    conditions) along with the terms and conditions contained in this Agreement comprehensively account for all the terms and conditions
                    under which the Data Consumer is approved to use/adapt/share the Data concerned (as detailed in section 1. Data of this Agreement).
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Data Integrity:</b>
                  &nbsp;<span>
                    The Data Provider declares that the Data concerned (as detailed in section 1. Data of this Agreement) is free of any
                    collection/operational/technical errors to the best of its knowledge and the integrity of the Data concerned has been ensured through
                    the various stages of collection, management, aggregation/anonymisation (if any) and distribution operations.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Exempted Data/Information:</b>
                  &nbsp;<span>
                    The Data Provider declares that the Data concerned (as detailed in section 1. Data of this Agreement) do not contain any of the
                    following types of data/information identified as personal/sensitive/non-shareable by Acts/Rules of Government of India:
                  </span>
                </li>
                <ol type="i" class="childlisting">
                  <li style="margin-bottom: 10px">Personal information or personally identifiable information</li>
                  <li style="margin-bottom: 10px">Names, crests, logos and other official symbols of the Data Provider</li>
                  <li style="margin-bottom: 10px">Data subject to intellectual property rights including patents, trade-marks and official marks</li>
                  <li style="margin-bottom: 10px">Military insignia</li>
                  <li style="margin-bottom: 10px">Identity documents</li>
                  <li style="margin-bottom: 10px">
                    Any data/information that cannot be publicly disclosed for grounds provided under section 8 of the Right to Information Act, 2005
                  </li>
                </ol>
              </ol>  
              
              <li style="font-weight: bold">Terms and Conditions for the Data Consumer</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">
                  <b>Lawful Uses of Data:</b>
                  &nbsp;<span>
                    The Data Consumer declares that the Data concerned (as detailed in section 1 of this Agreement), which has been made available via IDP
                    by the Data Provider and access to which is being provided to the Data Consumer via this Agreement, will be used only for lawful
                    purposes and under the specific conditions of the licence mentioned in section 2.c. of this Agreement.</span
                  >
                </li>
                <li style="margin-bottom: 10px">
                  <b>Attribution:</b>
                  &nbsp;<span>
                    The Data Consumer shall acknowledge the Data Provider, source DOI/URL/URI and licence of Data, when using/adapting/sharing the same,
                    through an attribution statement that shall include:
                  </span>
                </li>
                <ol>
                  <li style="margin-bottom: 10px">{organization.title}</li>
                  <li style="margin-bottom: 10px">{dataset_access_model.issued}</li>
                  <li style="margin-bottom: 10px">
                    https://{settings.BASE_DOMAIN}/datasets/{dataset_access_model.dataset.title.lower().replace(" ", "-") + "_" + dataset_access_model.dataset.id}
                  </li>
                  <li style="margin-bottom: 10px">{dataset_access_model.data_access_model.license.title}</li>
                </ol>
                <li style="margin-bottom: 10px">
                  <b>Non-endorsement:</b>
                  &nbsp;<span>
                    The Data Consumer shall not indicate or suggest in any manner that any specific use/adaptation/sharing of the Data concerned is either
                    endorsed or supported by the Data Provider.
                  </span>
                </li>
              </ol>
              
              <li style="font-weight: bold">Termination</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">
                  Failure by the Data Provider to comply with stipulated terms and conditions contained in this Agreement will cause automatic termination
                  of this Agreement.
                </li>
                <li style="margin-bottom: 10px">
                  Failure by the Data Consumer to comply with stipulated terms and conditions contained in this Agreement will cause automatic termination
                  of this Agreement.
                </li>
                <li style="margin-bottom: 10px">
                  Further, the Data Provider has all the rights to terminate this Agreement for any reason after giving a notice to the Data Consumer.
                </li>
                <li style="margin-bottom: 10px">
                  Upon termination of the Agreement, the Data Provider will forgo any future stream of payment of licence fees that may have been agreed
                  upon as part of this Agreement (if any).
                </li>
                <li style="margin-bottom: 10px">
                  Upon termination of the Agreement, the Data Consumer will immediately ensure that the Data concerned is no longer stored and used,
                  either publicly or in private.
                </li>
                <li style="margin-bottom: 10px">
                  Once the Agreement is terminated under the aforementioned clauses or any other Indian law, the Data Consumer may re-access the Data
                  concerned via IDP after the violation(s) due to which the Agreement was terminated are addressed and resolved.
                </li>
                <li style="margin-bottom: 10px">
                  For avoidance of doubt, this Agreement does not affect any rights that the Data Provider and/or the Data Consumer may have to seek
                  remedies for violation of this Agreement
                </li>
              </ol>
    
              <li style="font-weight: bold">Governing Law</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">This Agreement is governed by Indian law.</li>
                <li style="margin-bottom: 10px">
                  The courts of Delhi Jurisdiction shall have exclusive rights to entertain disputes between the parties.
                </li>
              </ol>
            </ol>
            <p style="text-align: center">***</p>
            <p>
              Data Provider and Data Consumer agree and acknowledge that this Agreement represents the entire agreement between. In the event that Data
              Provider and/or Data Consumer desire to change, add, or otherwise modify any terms contained in this Agreement, the same shall be done
              through mutual communication, agreement and re-accessing the Data concerned via IDP.
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
        body span {{
            line-height: 1.4;    
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
              <a href="{organization.homepage}">{organization.title}</a>, a {organization.organization_types} (hereinafter the “Data
              Provider”), and <a href="https://{settings.BASE_DOMAIN}">India Data Platform</a> (hereinafter the “IDP”) managed by National Informatics
              Centre, with its main office located in A-Block, Lodhi Road, CGO Complex, New Delhi, 110003, India.
            </p>
            <p>
              Whereas, Data Provider has collected/compiled/generated/harvested and/or controls/manages the data distributions specified in section 1.
              Data (hereinafter the “Data”),
            </p>
    
            <p>
              Whereas, Data Provider wishes to share the Data via IDP and to make it available for users of IDP to discover, access and use as per the
              access type(s), data access model(s), licence(s) and additional terms and conditions (if any) to be specified by the Data Provider,
            </p>
            <p>
              Whereas, Data Provider agrees to share the Data via IDP in agreement with the terms and conditions for the Data Provider specified in
              section 2. Terms and Conditions for the Data Provider in particular and in all sections of this Agreement in general, and
            </p>
            <p>
              Whereas, IDP agrees to make the Data available on IDP in agreement with the terms and conditions for IDP specified in section 3. Terms and
              Conditions for India Data Platform in particular and in all sections of this Agreement in general,
            </p>
            <p>
              In consideration of the above premises, and of the details of Data and mutual promises herein contained, the parties do hereby agree as
              follows:
            </p>
            <ol>
              <li style="font-weight: bold">Data</li>
              <p>
                The Data shared by the Data Provider, to be made available on IDP, through this Agreement signed on Date includes the following
                distributions and additional information (if any):
              </p>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px"><b>Distributions (Data/APIs)</b></li>
                {get_dataset_resource_details(dataset)}
    
                <li style="font-weight: bold">Terms and Conditions for the Data Provider</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">
                  <b>Authority to Share Data:</b>
                  &nbsp;<span
                    >The Data Provider declares that they have the full power and authority to accept these Terms and Conditions and to be the signatory
                    for this Data Sharing Agreement.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Approvals to Share Data (as applicable):</b>
                  &nbsp;<span>
                    The Data Provider has obtained all approvals, including any institutional, ethics and regulatory approvals, necessary to share the
                    data via IDP and for the storage, use and distribution of the data concerned by IDP.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Lawful Provision of Data: </b>
                  &nbsp;<span>
                    The Data Provider declares that the Data concerned (as detailed in section 1. Data of this Agreement), which is being shared via IDP,
                    has been lawfully collected/compiled/generated by the Data Provider and/or the Data Provider has the legal authority to
                    control/manage/share the Data Concerned. The Data Provider also confirms that sharing of the data via IDP, and the storage, use and
                    distribution of the data by IDP, will not infringe or invade any existing rights of third parties upon the data concerned (if any).
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Data Integrity: </b>
                  &nbsp;<span>
                    The Data Provider declares that the Data concerned (as detailed in section 1. Data of this Agreement) is free of any
                    collection/operational/ technical errors to the best of their knowledge and the integrity of the Data concerned has been ensured
                    through the various stages of collection, management, aggregation/anonymisation (if any) and distribution operations.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Exempted Data/Information:</b>
                  &nbsp;<span>
                    The Data Provider declares that the Data concerned (as detailed in section 1. Data of this Agreement) do not contain any of the
                    following types of data/information identified as personal/sensitive/ non-shareable by Acts/Rules of Government of India:
                  </span>
                </li>
                <ol type="i" class="childlisting">
                  <li style="margin-bottom: 10px">Personal information or personally identifiable information</li>
                  <li style="margin-bottom: 10px">Names, crests, logos and other official symbols of the Data Provider</li>
                  <li style="margin-bottom: 10px">Data subject to intellectual property rights including patents, trade-marks and official marks</li>
                  <li style="margin-bottom: 10px">Military insignia</li>
                  <li style="margin-bottom: 10px">Identity documents</li>
                  <li style="margin-bottom: 10px">
                    Any data/information that cannot be publicly disclosed for grounds provided under section 8 of the Right to Information Act, 2005
                  </li>
                </ol>
                <li style="margin-bottom: 10px">
                  <b>Data Review Process (As Applicable): </b>
                  &nbsp;<span>
                    The Data Provider agrees to submit the Data concerned, if and when required, to the Data Provider’s institutional review process
                    and/or to the data review mechanism implemented for IDP as specified by Competent Authority(ies).
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Grievance Redressal: </b>
                  &nbsp;<span>
                    The Data Provider agrees to cooperate with the administrators of IDP and/or other Competent Authority(ies) to address
                    legal/technical/other problems that may be identified in relation to the Data concerned.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Data Take Down Notice: </b>
                  &nbsp;<span>
                    The Data Provider agrees to cooperate with the administrators of IDP and/or other Competent Authority(ies) to address any concerns
                    raised in relation to the Data concerned through data Take Down Notice submitted by the user(s) of IDP. Refer to section 4.
                    Termination of this Agreement, especially sections 4.b. and 4.c., for details.
                  </span>
                </li>
              </ol>
    
              <li style="font-weight: bold">Terms and Conditions for India Data Platform</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">
                  <b>Sharing of Data via IDP:</b>
                  &nbsp;<span
                    >IDP is provided with a world-wide, non-exclusive approval by the Data Provider to make the Data concerned available, discoverable and
                    accessible on IDP to all users of the platform under data access model(s), type(s) of access, licence(s) and other terms and
                    conditions as selected by the Data Provider for the Data concerned.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Authentication-based Access to Data (If Applicable):</b>
                  &nbsp;<span>
                    If the Data Provider decides to share the Data concerned through authentication-based access, where Data Consumers interested in
                    accessing the Data will have to submit a Data Access Request for processing and approval either by the Data Provider or by an entity
                    specified by the Data Provider, IDP declares that the required Data Access Request submission and processing mechanism will be enabled
                    for the Data concerned.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Attribution: </b>
                  &nbsp;<span>
                    IDP declares that the Data Provider will be acknowledged as the original source and responsible entity for the Data concerned in all
                    places on IDP that the Data concerned is made available to user(s). IDP, however, will not be liable for failure of other external
                    entities/websites/users in acknowledging the Data Provider as the original source and responsible entity of the Data concerned.
                  </span>
                </li>
                <li style="margin-bottom: 10px">
                  <b>Data Integrity:</b>
                  &nbsp;<span>
                    IDP declares that the Data concerned will be made available to Data Consumer(s) as is, i.e., as shared/specified/transformed by the
                    Data Provider and without any modification to its content undertaken by IDP. Further, IDP provides no warranty to the user(s) of IDP
                    regarding the accuracy and quality of the Data concerned and is not liable for any harm that may be caused to the Data Provider(s)
                    and/or the Data Consumer(s) by sharing, accessing and using the Data concerned.</span
                  >
                </li>
              </ol>
              <li style="font-weight: bold">Termination</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">
                  Failure to comply with stipulated terms and conditions contained in this Agreement will cause automatic termination of this Agreement.
                </li>
                <li style="margin-bottom: 10px">
                  Failure to comply with the instructions given to the Data Provider by IDP on the basis of data Take Down Notice(s) submitted by the
                  user(s) of IDP will cause automatic termination of this Agreement.
                </li>
                <li style="margin-bottom: 10px">
                  Upon receipt of a data Take Down Notice, IDP will share the submission made by the user(s) of IDP concerned with the Data Provider along
                  with instructions to remedy the same (if and as applicable) and will stipulate a time period within which the remedial action may be
                  completed by the Data Provider to avoid termination of the Agreement.
                </li>
                <li style="margin-bottom: 10px">
                  Upon termination of the Agreement, IDP will immediately ensure that the Data concerned is no longer available for discovery, access and
                  usage to the user(s) of IDP. IDP, however, will not be liable for any harm that may be caused to the Data Provider by subsequent use of
                  the Data concerned by the Data Consumer(s) who already had access to the Data concerned prior to the date of termination.
                </li>
                <li style="margin-bottom: 10px">
                  Once the Agreement is terminated under the aforementioned clauses or any other Indian law, the Data Provider may re-share the Data
                  concerned via IDP after addressing and resolving the violation(s) concerned due to which the Agreement was terminated.
                </li>
                <li style="margin-bottom: 10px">
                  For avoidance of doubt, this Agreement does not affect any rights that the Data Provider and/or IDP may have to seek remedies for
                  violation of this Agreement.
                </li>
              </ol>
    
              <li style="font-weight: bold">Governing Law</li>
              <ol type="a" class="childlisting">
                <li style="margin-bottom: 10px">This Agreement is governed by Indian law.</li>
                <li style="margin-bottom: 10px">
                  The courts of Delhi Jurisdiction shall have exclusive rights to entertain disputes between the parties.
                </li>
              </ol>
            </ol>
            <p style="text-align: center">***</p>
            <p>
              Data Provider and IDP agree and acknowledge that this Agreement represents the entire agreement between. In the event that Data Provider
              and/or IDP desire to change, add or otherwise modify any terms contained in this Agreement, the same shall be done through mutual
              communication, agreement and re-sharing of the Data concerned via IDP.
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
