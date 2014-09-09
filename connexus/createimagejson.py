import json
import base64

#Encodes an image file into base64 and then sends to json object
#dumps the json object to a text file so it can be used in
#postman w/upload image
with open("amypic.jpg", "rb") as f:
    data = f.read()
    picdata = data.encode("base64")
mystructure = {'streamid':'12345', 'uploadimage':picdata, 'contenttype':'image/jpeg'}
myjson = json.dumps(mystructure)
jsonfile = open("myimagejson.txt",'w')
jsonfile.write(str(myjson))
jsonfile.close()
