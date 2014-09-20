import json
from datetime import datetime


currenttime = str(datetime.now())
viewdatelistempty = list()
streamsubscribers = ['amy_hindman@yahoo.com','aimers1975','bob@gmail.com']
taglist = ['#testtag']
commentlist = list()
imagelist = list()
mystructure = {'streamname':'amy1','creationdate':currenttime,'viewdatelist':viewdatelistempty,'currentuser':'amy_hindman@yahoo.com','subscribers':streamsubscribers,'tags':taglist,'coverurl':'www.google.com','commentlist':commentlist,'imagelist':imagelist}
myjson = json.dumps(mystructure)
jsonfile = open("createstreamsamplejson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()