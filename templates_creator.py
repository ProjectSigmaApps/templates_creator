import csv
import json
import requests
from requests.auth import HTTPBasicAuth
import PySimpleGUI as sg
import webbrowser

'''Bulk Template Creator 
Acts on a Merit Organization as an App to create templates in bulk.
A properly formatted CSV must be used, and the relavent org and app IDs must be submitted in the popup. Note, existing fields will be used when found, replacing the data in the spreadsheet for that field.
'''

class newTemplate:
    '''Template class
    A new instance of this class will be created for each valid row in the input file.
    '''
    def __init__(self, templateId='', title='', description='', canOnlyBeSentOnce=False, coverPhotoId='', coverPhotoFileName='', additionalFields=[]):
        self.templateId = templateId
        self.title = title
        self.description = description
        if canOnlyBeSentOnce == '' or 'FALSE':
            self.canOnlyBeSentOnce = False
        if canOnlyBeSentOnce == 'TRUE':
            self.canOnlyBeSentOnce = True
        self.coverPhotoId = coverPhotoId
        self.coverPhotoFileName = coverPhotoFileName
        self.additionalFields = additionalFields
        self.meritTemplateExists()

    def createTemplate(self):
        '''Template Creation
        Create a new template via API call to Merit; append returned ID to self.
        '''
        url = s.url + "merittemplates"
        payload = {
            "orgId": orgId,
            "title": self.title,
            "description": self.description,
            "canOnlyBeSentOnce": self.canOnlyBeSentOnce,
            "coverPhoto": {
              "id": self.coverPhotoId,
              "fileName": self.coverPhotoFileName
            }
        }
        headers = {
            'Content-Type': "application/json"
        }
        r = s.post(url, data=json.dumps(payload), headers=headers).json()
        self.templateId = r['id']

    def meritTemplateExists(self):
        '''Check if that template already exists by matching the `title`; update `id` and `description` if so. Create if not.'''
        existingTemplates = getTemplates()
        for meritTemplate in existingTemplates['merittemplates']:
            if self.title == meritTemplate['title']:
                self.templateId = meritTemplate['id']
                self.description = meritTemplate['description']
                return
        self.createTemplate()

    def toDict(self):
        return {
            'id': self.templateId,
            'title': self.title,
            'description': self.description,
            'canOnlyBeSentOnce': self.canOnlyBeSentOnce,
            'additionalFields': self.additionalFields
        }

class newField:
    '''Class for additional fields
    All fields will be created as an instance of this class, and then appended to the template once complete.
    '''
    def __init__(self, fieldId='', name='', fieldType='', description='', newEnabled=False, newRequired=False, newValueForAllMerits=''):
        self.fieldId = fieldId
        self.name = name
        self.fieldType = fieldType
        self.description = description
        if newEnabled == '' or 'FALSE':
            self.newEnabled = False
        if newEnabled == 'TRUE':
            self.newEnabled = True
        if newRequired == '' or 'FALSE':
            self.newRequired = False
        if newRequired == 'TRUE':
            self.newRequired = True
        self.newValueForAllMerits = newValueForAllMerits
        self.fieldExists()

    def createField(self):
        '''Create New Fields
        If a field is included that does not already exist, this function will be called to create the field via an API call to Merit and update self.fieldId.
        '''
        url = s.url + "fields"
        payload = {
            "orgId": orgId,
            "name": self.name,
            "description": self.description,
            "fieldType": self.fieldType
        }
        headers = {
            'Content-Type': "application/json"
        }
        r = s.post(url, data=json.dumps(payload), headers=headers).json()
        self.fieldId = r['id']

    def fieldExists(self):
        '''Field Exists
        Checks if a given field exists by checking for its name in the list of Org Fields.
        '''
        fieldList = getFields()
        for field in fieldList['fields']:
            if self.name == field['fieldName']:
                self.fieldId = field['id']
                self.fieldType = field['fieldType']
                self.description = field['description']
                return
        self.createField()

    def toDict(self):
        '''Returns the newField instance as a Dict for consistent handling.'''
        return {
            'id': self.fieldId,
            'name': self.name,
            'fieldType': self.fieldType,
            'description': self.description,
            'newEnabled': self.newEnabled,
            'newRequired': self.newRequired,
            'newValueForAllMerits': self.newValueForAllMerits
        }

def auth(orgId, appId, appSecret):
    '''Auth
    Takes orgId, appId, and appSecret as input to retreive an orgAccessToken via call to Merit API.
    If the App has not been linked to this Org yet, it will request and provide the appLink URL then retry the orgAccessToken request.
    The orgAccessToken is currently not rechecked after being successfully obtained, because no run of this script should exceed the 1hr expiry on the token.
    '''
    while True:
        rAuth = s.post(s.url + 'orgs/' + orgId + '/access',
                       auth=HTTPBasicAuth(appId, appSecret))
        if rAuth.status_code == 200:
            rAuthJson = rAuth.json()
            orgAccessToken = rAuthJson['orgAccessToken']
            return {'Authorization': 'Bearer ' + orgAccessToken}
        if rAuth.status_code == 403:
            # fetch applink url
            payload = {"requestedPermissions": [{"permissionType": "CanManageAllMeritTemplates"}, {
                "permissionType": "CanSendAllMeritTemplates"}], "successUrl": "/goodpath", "failureUrl": "/badpath", "state": "somestatevariable"}
            headers = {
                'Content-Type': "application/json"
            }
            rLink = s.post(s.url + 'request_linkapp_url',
                           auth=HTTPBasicAuth(appId, appSecret), data=json.dumps(payload), headers=headers).json()
            linkUrl = rLink['request_linkapp_url']
            sg.Popup(
                'Please click OK to follow the below URL and link this app with the desired Org:', linkUrl)
            webbrowser.open_new(linkUrl)
            sg.Popup(
                'Click OK once you have linked your Org to continue')

def getTemplates():
    '''Updates existing templates list. Limit set to 500, if greater must update tool to handle pagination.'''
    rt = s.get(s.url+'orgs/'+orgId+'/merittemplates?limit=500')
    return rt.json()

def getFields():
    '''Update existing fields list. Limit set to 500, if greater must update tool to handle pagination'''
    rf = s.get(s.url+'orgs/'+orgId+'/fields?limit=500')
    return rf.json()

def userInput():
    '''User input
    text input for orgId, appId, and appSecret
    file upload prompt to select .csv
    '''
    layout = [
        [sg.Text('Please enter your orgId, appId, and appSecret and select your CSV')],
        [sg.Text('orgId', size=(15, 1)), sg.InputText(key='orgId')],
        [sg.Text('appId', size=(15, 1)), sg.InputText(key='appId')],
        [sg.Text('appSecret', size=(15, 1)), sg.InputText(key='appSecret', password_char='*')],
        [sg.Text('File')], [sg.Input(), sg.FileBrowse()],
        [sg.Combo(('Staging', 'Sandbox', 'Production'),
                  key='Environment', size=(10, 1), default_value='Sandbox')],
        [sg.Submit(), sg.Cancel()]
    ]
    window = sg.Window(
        'Basic Authentication and file selection', layout, finalize=True)
    while True:
        event, values = window.Read(timeout=100)
        if values['Environment'] == 'Staging':
            values['Environment'] = 'https://qwebhjklr-api.merits.com/v2/'
        if values['Environment'] == 'Sandbox':
            values['Environment'] = 'https://sandbox-api.merits.com/v2/'
        if values['Environment'] == 'Production':
            values['Environment'] = 'https://api.merits.com/v2/'
        if event is (None, 'Cancel'):
            window.Close()
            break
        if event == 'Submit':
            window.Close()
            return values.values()
    window.Close()

def templatesFileValidation(templatesCSV):
    '''File validation
    Read a CSV file to ensure the formatting is as required for ingestion.
    '''
    headerRow = ['meritTemplate.title', 'meritTemplate.description', 'meritTemplate.canOnlyBeSentOnce', 'meritTemplate.coverPhotoId', 'meritTemplate.coverPhotoFileName', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits', 'field.name', 'field.fieldType', 'field.description', 'field.newEnabled', 'field.newRequired', 'field.newValueForAllMerits']
    sg.Popup('Click OK to begin CSV validation.', 'Note, this may take a few minutes. You will be notified if errors are found or if validation passes successfully.')
    with open(templatesCSV) as infile:
        sheet = list(csv.reader(infile))
        for num, row in enumerate(sheet):
            for col, cell in enumerate(row):
                if num == 0:
                    if cell != headerRow[col]:
                        sg.PopupScrolled('An error has been found with your header row. Please ensure it follows the below format exactly, even if all 35 fields are not utilized in your templates:', 'meritTemplate.title, meritTemplate.description , meritTemplate.canOnlyBeSentOnce, meritTemplate.coverPhotoId, meritTemplate.coverPhotoFileName, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits')
                        return False
                elif sheet[0][col] != 'field.newValueForAllMerits' and cell == '':
                    breakMessage = 'Error, this cell cannot be blank. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                    sg.PopupError(breakMessage)
                    return False
                else:
                    if sheet[0][col] == 'meritTemplate.title' and len(cell) > 60:
                        breakMessage = 'Error, Template Title is too long. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'meritTemplate.description' and len(cell) > 160:
                        breakMessage = 'Error, Template Description is too long. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'meritTemplate.canOnlyBeSentOnce' and cell not in ['TRUE', 'FALSE']:
                        breakMessage = 'Error, value must be exactly TRUE or FALSE. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'meritTemplate.coverPhotoId' and len(cell) != 24:
                        breakMessage = 'Error, template IDs are expected to be 24 characters in length. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'meritTemplate.coverPhotoFileName' and len(cell) > 160:
                        breakMessage = 'Error, please use a smaller fileName (less than 155 characters). Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'field.name' and len(cell) > 35:
                        breakMessage = 'Error, Field Name is too long. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'field.fieldType' and cell not in['ShortText', 'LongText', 'Date', 'Checkbox', 'Documents', 'Photos', 'Videos', 'Name']:
                        breakMessage = 'Error, Field Type must be exactly one of the following: ShortText, LongText, Date, Checkbox, Documents, Photos, Videos, or Name. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'field.description' and len(cell) > 160:
                        breakMessage = 'Error, Field Description is too long. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
                    if sheet[0][col] == 'field.newEnabled' and cell not in ['TRUE', 'FALSE']:
                        breakMessage = 'Error, value must be exactly TRUE or FALSE. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False                    
                    if sheet[0][col] == 'field.newRequired' and cell not in ['TRUE', 'FALSE']:
                        breakMessage = 'Error, value must be exactly TRUE or FALSE. Please correct your CSV and retry. Row: ' + str(num + 1) + ' Col: ' + str(col + 1)
                        sg.PopupError(breakMessage)
                        return False
    sg.Popup('CSV Successfully Validated. Press OK to continue.')
    return True

def templatesFileIngestion(templatesCSV):
    '''File ingestion
    Read a properly formatted CSV into the template and field classes, ending in a structured dict.
    Columns 0-2 are for the template itself, and every set of 6 columns after that repeat for each additional field to be added (max 35 additional fields). 
    Formatted CSV Header Row:
    meritTemplate.title,meritTemplate.description,meritTemplate.canOnlyBeSentOnce, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits, field.name, field.fieldType, field.description, field.newEnabled, field.newRequired, field.newValueForAllMerits
    '''
    tList = []
    tListPos = 0
    index = 0
    templatesCount = 0
    with open(templatesCSV) as infile:
        sheet = list(csv.reader(infile))
        templatesCount = len(sheet)
        for row in sheet:
            sg.OneLineProgressMeter('Template and Field Creation Progress', index,
                                    templatesCount, 'key', 'Total templates to be processed:')
            index += 1
            if row[0] != 'meritTemplate.title':
                myTemplate = newTemplate(
                    '', row[0], row[1], row[2], row[3], row[4], [])
                tList.append(myTemplate.toDict())
                for cell in range(len(row)):
                    if (row[cell] is not '' or None) and (sheet[0][cell] == 'field.name'):
                        myField = newField(
                            '', row[cell], row[cell+1], row[cell+2], row[cell+3], row[cell+4], row[cell+5])
                        tList[tListPos]['additionalFields'].append(
                            myField.toDict())
                tListPos += 1
    return tList

def createFieldSettings(templatesDict):
    '''Creates fieldSettings after all templates and additional fields have been processed (field+template)'''
    totalLength = 0
    index = 0
    for temp in templatesDict:
        totalLength += 1
        for field in temp['additionalFields']:
            if field['name'] is not '' or None:
                totalLength += 1
    for template in templatesDict:
        for field in template['additionalFields']:
            sg.OneLineProgressMeter('Field Setting Creation Progress', index,
                                    totalLength, 'key', 'Total fields to be added to templates:')
            index += 1
            if field['name'] is not '' or None:
                url = s.url + "merittemplates/" + \
                    template['id'] + '/fields/' + field['id']
                payload = {
                    'newEnabled': field['newEnabled'],
                    'newRequired': field['newRequired']
                }
                if field['newValueForAllMerits'] is not '' or None:
                    payload.update(
                        {'fieldId': field['id'], 'newValueForAllMerits': field['newValueForAllMerits']})
                headers = {
                    'Content-Type': "application/json"
                }
                s.post(url, data=json.dumps(payload), headers=headers)

if __name__ == '__main__':
    orgId, appId, appSecret, templatesCSV, filePath, server = userInput()

    s = requests.Session()
    s.url = server
    s.headers.update(auth(orgId, appId, appSecret))

    valid = templatesFileValidation(templatesCSV)
    if valid:
        newTemplates = templatesFileIngestion(templatesCSV)
        createFieldSettings(newTemplates)