import json
import base64
import uuid

myuser = {'userid':'amy@gmail.com'}
myjson = json.dumps(myuser)
jsonfile = open("myuserjson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()