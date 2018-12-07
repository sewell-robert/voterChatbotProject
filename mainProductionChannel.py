import requests
import json

##############################################################################################################################################################################
#Add voter to TextIt.in contacts if canvasser initiates enrollment
if input_data.get('voterPhone') != None:
    
    #Get canvasser contact info to be stored in user's contact fields
    url_canvasser = "https://api.textit.in/api/v2/contacts.json"
    headers_canvasser = {
        "Authorization": "Token ",
        "Content-Type": "application/json"
    }
    params_canvasser = {
        "urn": input_data.get('urn')
    }

    r = requests.get(url=url_canvasser, headers=headers_canvasser, params=params_canvasser)

    canvasserContactInfo = r.json()
    results = canvasserContactInfo.get('results')[0]
    canvasserName = results.get('name')

    if canvasserName == None:
        canvasserName = "N/A"
        
    fields = results.get('fields')
    triggerWord = fields.get('trigger_word')
    
    if triggerWord == "Proxy29":
        groups = ["811beffc-d2ec-4a8c-83c9-fe3a6a458206"]
    elif triggerWord == "Proxy30":
        groups = ["136f79e7-6411-4687-b691-f30adf022cf4"]
    else:
        groups = []
        
    #Set up voter name for TextIt Explorer API POST request payload
    voterFullName = input_data.get('voterFirstName') + " " + input_data.get('voterLastName')

    #POST request to TextIt Explorer API to add new user to contacts
    explorer_url = "https://api.textit.in/api/v2/contacts.json"
    explorer_headers = {
        'Authorization': 'Token ',
        'Content-Type': 'application/json'
    }
    explorer_payload = {
        "name": voterFullName,
        "language": "eng",
        "urns": ["tel:" + input_data.get('voterPhone')],
        "groups": groups,
        "fields": {
          "firstname": input_data.get('voterFirstName'),
          "lastname": input_data.get('voterLastName'),
          "checkedtwice": "false",
          "canvasser_name": canvasserName,
          "canvasser_phone": input_data.get('urn'),
          "trigger_word": triggerWord,
          "switch1": "On"
        }
    }

    r2 = requests.post(url=explorer_url, headers=explorer_headers, data=json.dumps(explorer_payload))
    print(r2.status_code)
##############################################################################################################################################################################
        
#Create headers and POST body
url = "https://api.securevan.com/v4/people/find"
get_url = "https://api.securevan.com/v4/people/"
get_expand_url = "?&$expand=phones,emails,addresses,districts"

headers = {
    'Content-Type' : 'application/json',
    'Authorization' : 'Basic '
}

auth = ('username', 'password')
returnAddress = None
district = None

#Split on contact full name - its the only value that persists between 
#textit triggers, as far as I could tell
if input_data.get('voterPhone') != None:
    name = input_data.get('voterFirstName') + " " + input_data.get('voterLastName')
    splitNames = name.split()
else:
    name = input_data.get('fullName')
    splitNames = name.split()

#Split phone number into format expected by VoteBuilder
streetAddress = input_data.get('streetAddress')
if streetAddress is None:
    if input_data.get('voterPhone') is None:
        phone = input_data.get('urn')
        phone = phone.split('+')
        phone = phone[1]
    #phone = phone[0] + '-' + phone[1] + phone[2] + phone[3] + '-' + phone[4] + phone[5] + phone[6] + '-' + phone[7] + phone[8] + phone[9] + phone[10]  
    else:
        phone = input_data.get('voterPhone')
        phone = phone.split('+')
        phone = phone[1]
else:
    if input_data.get('voterPhone') is None:
        phone = input_data.get('urn')
    else:
        phone = input_data.get('voterPhone')
    
#Body of VoteBuilder request
payload = {
    'firstName': splitNames[0],
    'lastName': splitNames[1],
    'dateOfBirth': input_data.get('dob'),
  
    'addresses': [
        {
            'addressLine1': input_data.get('streetAddress'),
            'zipOrPostalCode': input_data.get('zip5')
        }
    ],
    'phones': [
        {
            'phoneNumber': phone
        }
    ]
}
#email not used anymore
#if input_data.get('email') != None:
    #payload['emails'] = [ {'email': input_data.get('email'),} ]

#Make VoteBuilder API request
r = requests.post(url, headers=headers, auth=auth, data=json.dumps(payload))

#Extract response as JSON object
returnValue = r.json()

if returnValue.get('vanId') != None:  
    r = requests.get( get_url + str(returnValue.get('vanId')) + get_expand_url, headers=headers, auth=auth)
    getReturnValue = r.json()
    address = getReturnValue.get('addresses')
        
    #Get district number 
    districts = getReturnValue.get('districts')
    
    for field in districts:
        if field.get('name') == "State House":
            districtFieldValues = field.get('districtFieldValues')[0]
            district = districtFieldValues.get('name')
            
    #Checks that address with "isPreferred" set to true is returned
    for entry in address:
        if entry.get('isPreferred') == True:
            addressLine1 = entry.get('addressLine1')
            addressLine2 = entry.get('addressLine2')
            city = entry.get('city')
            state = entry.get('stateOrProvince')
            zipOrPostalCode = entry.get('zipOrPostalCode')
            returnAddress = addressLine1
            if addressLine2 != None:
                returnAddress = returnAddress + '\n' + addressLine2
            returnAddress = returnAddress + '\n' + city + ', ' + state + ' ' +  zipOrPostalCode
            break
        else:
            mainAddress = address[0]
            addressLine1 = mainAddress.get('addressLine1')
            addressLine2 = mainAddress.get('addressLine2')
            city = mainAddress.get('city')
            state = mainAddress.get('stateOrProvince')
            zipOrPostalCode = mainAddress.get('zipOrPostalCode')
            returnAddress = addressLine1
            if addressLine2 != None:
                returnAddress = returnAddress + '\n' + addressLine2
            returnAddress = returnAddress + '\n' + city + ', ' + state + ' ' +  zipOrPostalCode
    

#Set the data we return to textit
output = {
    'vanId': returnValue.get('vanId'),
    'address': returnAddress,
    'district': district,
    'PhoneOutput': 'tel:+' + phone