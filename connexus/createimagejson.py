import json
import base64


with open("amypic.jpg", "rb") as f:
    data = f.read()
    picdata = data.encode("base64")
mystructure = {'streamid':'12345', 'uploadimage':picdata, 'contenttype':'image/jpeg'}
myjson = json.dumps(mystructure)
jsonfile = open("myimagejson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()
