import os
filename = 'myfile.b'
(name,extension) = os.path.splitext(filename) 
print "File name: " + name 
print "File extension: " + extension 

if extension == '.gif':
  contenttype = 'image/gif'
elif extension == '.jpg':
  contenttype = 'image/jpeg'
elif extension == '.png':
  contenttype = 'image/png'
else:
  contenttype = None

print contenttype
