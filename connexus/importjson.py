import json

jsoninput = {'userid':1234,'streamname':'amystream','subscriberlist':['subscriber1','subscriber2'],'taglist':['tag1','tag2'],'url':'amy@yahoo.com'}
myfile = open('currentjson.txt','w')
data = json.dumps(jsoninput)
myfile.write(str(data))
myfile.close()