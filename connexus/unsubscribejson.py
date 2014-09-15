import json



mystructure = {'streamname':'amy1', 'unsubuser':'amy@gmail.com'}
myjson = json.dumps(mystructure)
jsonfile = open("unsubscribeuserjson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()
