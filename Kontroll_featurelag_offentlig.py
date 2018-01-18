#-------------------------------------------------------------------------------
# Name:        Kontroll av featurelag
# Purpose:     Et script som skal kontrollere et featurelag etter endringer og så sende en epost med oppdatering
#
# Author:      tobors
#
# Created:     18.01.2018
# Copyright:   (c) tobors 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import urllib2, json, urllib, datetime, time, smtplib
from datetime import timedelta
from time import strftime

# Variables
username = ''        # AGOL Username
password = ''    # AGOL Password

statusMelding = True    #Send statusmelding uansett om det ikke er lagt til nye objekter. 'False' hvis ikke

URL = 'https://services1.arcgis.com/oc32TmBcUxTXagmW/ArcGIS/rest/services/Fartsgrensevedtak_jan2018/FeatureServer/0/query'       # Feature Service URL. !Viktig å ha med query på slutten!

uniqueID = 'ID'           # i.e. OBJECTID
dateField = 'Dato_lagt_til_'      # Date field to query
hoursValue = 24                 # Number of hours to check when a feature was added

fromEmail = 'XXXXX@XXXX.XXX' # Email sender
toEmail = 'XXXXX@XXXX.XXX'   # Email receiver(s)
smtpServer = 'smtp.XXXX.XXX'    # SMPT Server Name
portNumber = XX                 # SMTP Server port

melding = ""
errorTitle = ""     #variabler som tar imot feilmeldingsdata hvis spørringen feiler
errorMessage = ""   #variabler som tar imot feilmeldingsdata hvis spørringen feiler

def parseError(error):      #funksjon for å behandle feilmeldinger og lage de som en lesbar tekst
    tidspunkt = strftime("%Y-%m-%d %H:%M:%S")
    errorTitle = "Fartsvedtak - Scriptet feilet"    #TODO: Legg inn funksjonalitet for å hente navn på featurelag automatisk
    errorMessage = "Error: {}\n{}\n{}\n\nKlarer feilmelding og test skript igjen.\n{}".format( data['error']['code'], "\n".join( data['error']['details']), data['error']['message'], tidspunkt)
    melding = [errorTitle, errorMessage]
    return melding


# Create empty list for uniqueIDs
oidList = []

#Denne bolken er bare nødvendig om man skal spørre opp mot et datalag som krever pålogging
### Generate AGOL token
##print('Generating Token')
##tokenURL = 'https://www.arcgis.com/sharing/rest/generateToken'
##params = {'f': 'pjson', 'username': username, 'password': password, 'referer': 'http://www.arcgis.com'}
##req = urllib2.Request(tokenURL, urllib.urlencode(params))
##response = urllib2.urlopen(req)
##data = json.load(response)
##
##if 'error' in data:     #sjekker om det eksisterer en feilmelding etter vi har spurt etter token
##    melding = parseError(data['error'])
##    token = ''
##else:       #hvis alt har gått smuuud, så hentes ut token
##    token = data['token']


# Query service and check if created_date time is within the last hour
# Hvis featurelag krever pålogging må bolken settes inn i if/else løkke
##if token:   #hvis scriptet har mottatt token, kjøres en spørring opp mot feature laget    #med pålogging

##params = {'f': 'pjson', 'where': "1=1", 'outfields' : '{0},{1}'.format(uniqueID, dateField), 'returnGeometry' : 'false', 'token' : token}  #med pålogging
params = {'f': 'pjson', 'where': "1=1", 'outfields' : '{0},{1}'.format(uniqueID, dateField), 'returnGeometry' : 'false'}    #uten pålogging
print u"----------Kjører spørring mot featurelag-------------\n\n"
req = urllib2.Request(URL, urllib.urlencode(params))
response = urllib2.urlopen(req)
data = json.load(response)

if 'error' in data:     #hvis det oppstår en feilmelding i spørringen blir den fanget opp her
    melding = parseError(data['error'])
else:       #hvis ikke går scriptet videre for å kontrollere når det siste objektet ble lagt til
    test = {}
    print u"----------Søker etter nye objekter-------------\n\n"
    for feat in data['features']:
        createDate = feat['attributes'][dateField]
        createDate = int(str(createDate)[0:-3])
        t = datetime.datetime.now() - timedelta(hours=hoursValue)
        t = time.mktime(t.timetuple())
        if createDate > t:
            test = feat
            oidList.append(feat['attributes']['ID'])

##else:   #hvis scriptet ikke har token så hopper det over til å sende en feilmelding til epostmottaker     #med pålogging
##    pass

def sendEmail():    #funksjon for å sende e-post
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT).decode('utf-8')
    smtpObj = smtplib.SMTP(host=smtpServer, port=portNumber)
    print "----------Sender e-post-------------\n\n"
    smtpObj.sendmail(FROM, TO, message)
    print "----------E-post sendt-------------\n\n"
    smtpObj.quit()


# Email Info
FROM = fromEmail
TO = [toEmail]

# If new features exist, send email
if len(oidList) > 0:
    SUBJECT = "Fartsgrensevedtak - nytt objekt lagt til i kartet"
    TEXT = "{0} objekt(er) med {1} {2} har blitt lagt til.\n\n{3}".format(len(oidList),uniqueID, ", ".join([str(x) for x in sorted(oidList)]),strftime("%Y-%m-%d %H:%M:%S"))
    sendEmail()
# Hvis en feilmelding eksisterer send epost med dette
elif melding:
    SUBJECT = melding[0]
    TEXT = melding[1]
    sendEmail()
#Hvis det er ønsket å sende statusmelding selv om det ikke er funnet nye objekter, gjøres det her
elif statusMelding:
    print errorMessage
    SUBJECT = 'Fartsgrensevedtak - kontroll: ingen objekter lagt til'
    TEXT  = 'Ingen nye objekter er lagt til de siste {} timene. \n\n{}'.format(hoursValue,strftime("%Y-%m-%d %H:%M:%S"))
    sendEmail()
#Hvis ikke så er vi ferdig for i dag
else:
    print u"----------Bruker har valgt å ikke sende melding når ingen nye objekter er funnet.-------------\n\n"
    pass



