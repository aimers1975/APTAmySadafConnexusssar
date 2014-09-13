import json



mystructure = {'streamname':'poop', 'pagerange': [0,1]}
myjson = json.dumps(mystructure)
jsonfile = open("mystreamandpagesjson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()
