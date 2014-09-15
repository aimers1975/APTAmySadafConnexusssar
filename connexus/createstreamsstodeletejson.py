import json



mystructure = {'streamstodelete':['amy1', 'amy2']}
myjson = json.dumps(mystructure)
jsonfile = open("deletestreamsamplejson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()