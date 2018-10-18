import requests
import json

#######################################################################################

#Narrows down election records to current election and returns vote status
def get_voteStatus(electionRecords):
    votingIndications = ["Y", "M", "A", "YD", "YR", "MD", "MR", "AD", "AR"]
    
    for election in electionRecords:
        name = election.get('electionRecordType')
        participation = election.get('participation')
        
        if name == "2018 - General" and participation in votingIndications:
            return {"voteStatus": "Yes!"} 
        
    return {"voteStatus": "No"}
    
#######################################################################################

#GET request to VoteBuilder for election records
def get_electionRecords(vandId):
    url = "https://api.securevan.com/v4/people/" + vandId + "?$expand=electionRecords"
    headers = {
    'Content-Type' : 'application/json',
    'Authorization' : 'Basic '
}
    auth = ('username', 'API KEY')

    r = requests.get(url=url, headers=headers, auth=auth)

    #Extract the response as a JSON object
    getReturnValue = r.json()
    electionRecords = getReturnValue.get('electionRecords')
    
    return get_voteStatus(electionRecords)

#######################################################################################

#GET request to Google Civic Info API
#Returns JSON object
def get_GoogleCivicInfoJSON(addressLine1):
    url = "https://www.googleapis.com/civicinfo/v2/voterinfo?key= "

    headers = {
        'Content-Type' : 'application/json'
    }
    
    #Convert addressLine1 plain string text to unicode before making into params
    #addressLine1 = unicode("9051 Renner Blvd Apt 3002 Lenexa KS", "utf-8")
    #addressLine1 = unicode(addressLine1, "utf-8")
    
    addressLine1 = addressLine1.split(" ")
    #addressLine1 = ['9051', 'Renner', 'Blvd', 'Lenexa', 'KS']
    params = {}
    value = ""
    for val in addressLine1:
        value = value + val + " "

    #electionId either needs to be ommited from the query params or correct ID needs to be found using the Google Civic Info elections query
    params.update({'electionId': 6000})
    params.update({'address': value})
    
    r = requests.get(url=url, headers=headers, params=params)

    #Extract the response as a JSON object
    getReturnValue = r.json()
    
    return getReturnValue

#######################################################################################

#determine closest early voting site from user's zip
def earlyVotingSiteMatch(zip):
    earlyVoteSiteDict = {'Johnson County Arts and Heritage Center': '66206, 66207, 66208, 66212, 66214, 66282',
                         'Hilltop Campus - Blue Valley': '66085, 66209, 66210, 66211, 66213, 66221, 66223, 66224, 66225, 66251, 66283',
                         'Johnson County Northeast Offices': '66201, 66202, 66203, 66204, 66205, 66222, 66276, 66286',
                         'Okun Fieldhouse': '66216, 66217, 66218, 66226, 66227',
                         'Johnson County Election Office': '66021, 66030, 66031, 66062, 66083, 66215, 66285',
                         'Johnson County Sunset Office Building': '66018, 66051, 66061, 66063, 66219, 66220, 66250'
                         }
    
    for key, value in earlyVoteSiteDict.iteritems():
        if zip in value:
            return key
        
    return "Johnson County Election Office"

#######################################################################################

#Get JSON object from Google Civic Info API and then parse object for early voting info
def get_earlyVotingInfo(addressLine1, zip, day):
    
    getReturnValue = get_GoogleCivicInfoJSON(addressLine1)
    earlyVoteSiteMatch = earlyVotingSiteMatch(zip)
    
    earlyVoteSites = getReturnValue.get('earlyVoteSites')
    for site in earlyVoteSites:
        address = site.get('address')
        if address.get('locationName') == earlyVoteSiteMatch:
            locationName = address.get('locationName')
            line1 = address.get('line1')
            city = address.get('city')
            state = address.get('state')
            zip = address.get('zip')
    
    earlyVoteSites1 = earlyVoteSites[0]
    pollingHours = earlyVoteSites1.get('pollingHours').split("\n")
    
    for set in pollingHours:
        if day in set:
            hours = set.split(":")[1]
    
   
    #Set the data we return to textit
    return {'locationName': locationName, 'line1': line1, 'city': city, 'state': state, 'zip': zip, 'hours': hours}

#######################################################################################

#Gets contest data from JSON and then creates HTML block to build the Google Docs sample ballot for each user
def get_sampleBallotInfo(addressLine1):
    data = get_GoogleCivicInfoJSON(addressLine1)
    contests = data.get('contests')
            
    contestsDict = {}
    contestsList = []
    for contestsNode in contests:
        
        if 'office' in contestsNode:
            contest = "<br /><b><p>" + contestsNode['office'] + ":" + "</p></b>"

        if 'candidates' in contestsNode:
            for candidates in contestsNode['candidates']:
                
                contest = contest + "<p>" + candidates['name']
                
                if 'party' in candidates:
                    party = candidates['party']
                    contest = contest + " " + " (" + party + ")"
                
                if 'candidateUrl' in candidates:
                    candidateUrl = candidates['candidateUrl']
                    
                    if candidateUrl[len(candidateUrl) - 1] == "/":
                        candidateUrl = candidateUrl[:-1]
                        
                    contest = contest + " | " + "<a href=" + candidateUrl + ">" + candidateUrl.split('//')[1] + "</a>"
                    
                if 'channels' in candidates:
                    channels = candidates['channels']
                    for channel in channels:
                        channelId = channel['id']
                        contest = contest + " | " + "<a href=" + channelId + ">" + channelId.split('//')[1] + "</a>"
                
                contest = contest + "</p></n>"
                
            contestsList.append(contest)
     
    contestsString = "".join(contestsList)
    contestsDict.update({'contests': contestsString})                 

    return contestsDict

#######################################################################################

#Get "Voters" group data out of TextIt database
def get_groupData():
    url = "https://api.textit.in/api/v2/contacts.json"
    headers = {'Authorization': 'Token '}
    params = {'group': "Voters"}
    
    r = requests.get(url=url, headers=headers, params=params)
    
    getReturnValue = r.json()
    
    return getReturnValue  

#######################################################################################

#Build data arrays with the group data from TextIt
def buildDataArrays():
    addressArray = []
    vanIdArray = []
    firstNameArray = []
    voteStatusArray = []
    urnArray = []

    groupData = get_groupData()
    results = groupData.get('results')
    for result in results:
        fields = result.get('fields')
        address = fields.get('addressline1')
        addressArray.append(address)
        vanId = fields.get('vanid')
        vanIdArray.append(vanId)
        firstName = fields.get('firstname')
        firstNameArray.append(firstName)
        voteStatus = fields.get('vote_status')
        voteStatusArray.append(voteStatus)
        urn = result.get('urns')[0]
        urnArray.append(urn)
            
    return {'addressArray': addressArray, 'vanIdArray': vanIdArray, 'firstNameArray': firstNameArray, 'voteStatusArray': voteStatusArray, 'urnArray': urnArray}

#######################################################################################

#For each user check VoteBuilder if they have already voted in the current election
#If yes, send status to TextIt to update user and stop early voting flows
#If user hasn't voted, get closest early voting site and hours out of the Google Civic Info API and start user in TextIt flow
#If user's vote status from TextIt contact field is "None" (user's first time in this channel), created personalized
#sample ballot to be sent in the flow
dataArrays = buildDataArrays()

firstNameArray = dataArrays.get('firstNameArray')

#Remove zip from each address and create new zip array
addressArray = dataArrays.get('addressArray')
finalAddressArray = []
zipArray = []
for address in addressArray:
    address = address.split(" ")
    zip = address.pop()
    address = " ".join(address)
    address = address.split(",")
    address = " ".join(address)
    finalAddressArray.append(address)

vanIdArray = dataArrays.get('vanIdArray')

voteStatusArray = dataArrays.get('voteStatusArray')

urnArray = dataArrays.get('urnArray')

day = input.get('day').split(",")[0]

#start user in early voting flow with status or polling location/hours if user hasn't voted yet
for i, vanId in enumerate(vanIdArray):
    status = get_electionRecords(vanId)
    
    url = "https://api.textit.in/api/v2/flow_starts.json"
    headers = {"Authorization": "Token ",
               "Content-Type": "application/json"}
    data = {"flow":"dda5eecc-5c86-4123-b196-13c98b049066", 
            "urns":[urnArray[i]]
           }    
 
    if status.get('voteStatus') == "Yes!":
        data.update({"extra": status})
        
        #Make POST request to TextIt.in initiating flow
        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        #print(r.status_code, r.reason)
    else:
        pollingLocation = get_earlyVotingInfo(addressArray[i], zip[i], day)
        
        status.update(pollingLocation)
        data.update({"extra": status})
        
        r = requests.post(url=url, headers=headers, data=json.dumps(data))

    #Get sample ballot data if user's first time in the flow then send over to the buildSampleBallot zap
    if voteStatusArray[i] == None:
        contests = get_sampleBallotInfo(addressArray[i])
        contests.update({'firstName': firstNameArray[i]})
        contests.update({'phone': urnArray[i].split('+')[1]})

        zap_url = "https://hooks.zapier.com/hooks/catch/3464149/lruys2/"
        zap_headers = {"Content/Type": "application/json"}
        zap_data = contests

        r_zap = requests.get(url=zap_url, headers=zap_headers, data=json.dumps(zap_data))