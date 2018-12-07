import requests
import json

#POST request to VoteBuilder to check if voter record was created
#If voter record exists, collect voter's vanId
def checkVoterRecord(firstName, lastName, zip5, dob):
    url = "https://api.securevan.com/v4/people/find"
    headers = {
    'Content-Type' : 'application/json',
    'Authorization' : 'Basic '
}
    auth = ('username', 'password')
    payload = {
        'firstName': firstName,
        'lastName': lastName,
        'dateOfBirth': dob,
        'addresses': [
            {
                'zipOrPostalCode': zip5
            }
        ]
    }
    
    r = requests.post(url=url, headers=headers, auth=auth, data=json.dumps(payload))
    print(r.status_code)
    
    getReturnValue = r.json()
    vanId = getReturnValue.get('vanId')
    
    return vanId
    
#######################################################################################
    
#GET request to VoteBuilder for voter's address and district
def get_VoterInfo(vandId):
    url = "https://api.securevan.com/v4/people/" + str(vandId) + "?$expand=addresses,districts"
    headers = {
    'Content-Type' : 'application/json',
    'Authorization' : 'Basic '
}
    auth = ('username', 'password')

    r = requests.get(url=url, headers=headers, auth=auth)
    print(r.status_code)
    
    voterInfo = []
    
    #Extract the response as JSON object
    getReturnValue = r.json()
        
    #Get district number 
    districts = getReturnValue.get('districts')
    
    for field in districts:
        if field.get('name') == "State House":
            districtFieldValues = field.get('districtFieldValues')[0]
            district = districtFieldValues.get('name')
            voterInfo.append(district)
            
    #Get address
    address = getReturnValue.get('addresses')
            
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
            
            voterInfo.append(returnAddress)
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
            
            voterInfo.append(returnAddress)
    
    return voterInfo

#######################################################################################

#Check VoteBuilder for users' voter records
#If voter record exists, get address and then update the user's TextIt contact info with vanId, address, and district
firstNamesArray = input.get('firstNamesArray').split(",")
lastNamesArray = input.get('lastNamesArray').split(",")
zip5Array = input.get('zip5Array').split(",")
dobArray = input.get('dobArray').split(",")
urnsArray = input.get('urnsArray').split(",")

for i, urn in enumerate(urnsArray):
    vanId = checkVoterRecord(firstNamesArray[i], lastNamesArray[i], zip5Array[i], dobArray[i])
    
    if vanId != None:
        voterInfo = get_VoterInfo(vanId)
        
        #Update contact in TextIt
        explorer_url = "https://api.textit.in/api/v2/contacts.json?urn=" + urn
        explorer_headers = {
            'Authorization': 'Token ',
            'Content-Type': 'application/json'
        }
        explorer_payload = {
            "groups": ["5e70ee06-fdac-4b92-b513-84232a21b00a"], #Will contact be removed from "Unregistered Voters" group?
            "fields": {
              "checkedtwice": "true",
              "vanid": vanId,
              "addressline1": voterInfo[1],
              "district": voterInfo[0]
            }
        }

        r = requests.post(url=explorer_url, headers=explorer_headers, data=json.dumps(explorer_payload))
        print(r.status_code)
        
        #Start registered voter in flow thanking him/her for registering
        #Pass in vanId
        url = "https://api.textit.in/api/v2/flow_starts.json"
        headers = {"Authorization": "Token ",
                   "Content-Type": "application/json"}
        data = {"flow":"9a477795-d5f3-409a-9253-16293fa4b6fc", 
                "urns":[urn],
                "extra": {"vanId": vanId}
               }    

        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        print(r.status_code)
        
    else:
        messageNumber = input_data.get('messageNumber')
        
        greetings = {'1': 'Good morning,', '2': 'Great day to register,', '3': 'Howdy,', '4': 'Thinking of you,', '5': 'Registration deadline is today,'}
        
        messages = {'1': 'October 16th is the final day to register to vote. Take a few minutes today to get it done!  -Vicky', '2': '“If people won’t vote for good candidates…because we think they won’t win, why will good candidates continue to run?”', '3': 'Did you know that less than 50% of eligible voters cast a vote in mid-term elections? We can do better!', '4': 'The clock is ticking. Democracy means “people-force.” Join your brothers and sisters of this great country and register to vote!', '5': 'Voting can make you Superman for one day, fighting for Truth, Justice, and the American Way! Hope to see you at the polls!'}
        
        url = "https://api.textit.in/api/v2/flow_starts.json"
        headers = {"Authorization": "Token ",
                   "Content-Type": "application/json"}
        data = {"flow":"9a477795-d5f3-409a-9253-16293fa4b6fc", 
                "urns":[urn],
                "extra": {
                    "greeting": greetings.get(messageNumber), 
                    "message": messages.get(messageNumber)
                         }
               } 
        print(data)
        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        print(r.status_code, r.reason)