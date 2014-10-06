import cloudstorage as gcs
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import files, images
from google.appengine.ext import db
from google.appengine.ext import blobstore, deferred
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import app_identity
from datetime import datetime,timedelta
from time import gmtime, strftime
from google.appengine.ext import ndb
import webapp2
import logging
import json
import cgi
import urllib
from urlparse import urlparse
import re
import os
import uuid
import base64
import string
import jinja2

#Probably not necessary to change default retry params, but here for example
my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
#TODO - Not sure this is the right place for this.
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
WEBSITE = 'https://blueimp.github.io/jQuery-File-Upload/'
MIN_FILE_SIZE = 1  # bytes
MAX_FILE_SIZE = 5000000  # bytes
IMAGE_TYPES = re.compile('image/(gif|p?jpeg|(x-)?png)')
ACCEPT_FILE_TYPES = IMAGE_TYPES
THUMBNAIL_MODIFICATOR = '=s80'  # max width / height
EXPIRATION_TIME = 300  # seconds

tmp_filenames_to_clean_up = []
gcs.set_default_retry_params(my_default_retry_params)
#this is the list of streams, keys are the userid that owns the stream, each value is a list of stream
ds_key = ndb.Key('connexusssar', 'connexusssar')

cronrate = 'five'
myimages = list()
cron_rate = -1
last_run_time = datetime.now()
first_run = False

AP_ID_GLOBAL = 'radiant-anchor-696.appspot.com'

VIEW_ALL_STREAM_HTML = """<div id="form_container"><form action="/ViewAllPageHandler" method="post"><div class="form_description"></div>
<table class="tg">
%s
</table>
</body></html>"""

EMAIL_HTML = """\
<html>
   <body>
      <form action="/emailHandler" method="post">
         <input name="toEmail" placeholder="To: ">
         <br/>
         <input name="subject" placeholder="Subject: ">
         <br/>
         <textarea name="message" style="height:200px; weight=500px;" placeholder="Enter your message: ">
         </textarea>
         <br/>
         <input type="submit" value="Send"/> 
      </form>
   </body>
</html>
"""

TRENDING_PAGE_STYLE = """
<style>
#section {
    width:350px;
    float:left;
    padding:10px;    
}
#aside {
    line-height:30px;
    height:300px;
    width:250px;
    float:right;
    padding:5px; 
    font-family: Arial, sans-serif; 
    font-size: 18px;
}
</style>
"""

TRENDING_STREAMS_HTML = """
<div id="form_container"><form><div class="form_description"></div><div id="section">
  <div id="trendingstreams"><H3>Top 3 Trending Streams</H3></div>
<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-right: solid 1px; border-left: solid 1px; border-top: none; border-bottom: none; border-width:1px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}
</style>
<table>
<tr>
%s
</tr>
</table>
</div>
"""

TRENDING_REPORT_HTML = """
<div id="form_container"><form><div class="form_description"></div><div id="aside">
    <br>
    <div id="trending"><H3>Email Trending Report<H3></div>
    <input type="checkbox" name="cronRate" value="No"> No reports<br>
    <input type="checkbox" name="cronRate" value="Five"> Every 5 minutes<br>
    <input type="checkbox" name="cronRate" value="Hour"> Every 1 hour<br>
    <input type="checkbox" name="cronRate" value="Day"> Every day<br>
    <input id="updaterate2" class="buttons" type="submit" value="Update Rate">
</div>
"""

SEARCH_STREAMS_HTML = """
<div id="form_container"><form><div class="form_description"></div><div id="aside">
   <form action="/SearchStreams" method="post">
     <input id="searchinput" name="searchString" placeholder="Stream Name:">
     <input id="Searchsubmit" type="submit" value="Search">
   </form>
</div>
"""

SEARCH_RESULT_HTML = """
<div id="article">
<form action="/ViewAllPageHandler" method="post">
  <style type="text/css">
  .tg  {border-collapse:collapse;border-spacing:0;}
  .tg tr {border:none;}
  .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-right: solid 1px; border-left: solid 1px; border-top: none; border-bottom: none; border-width:1px;overflow:hidden;word-break:normal;}
  .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}
  </style>
  <table width="500" cellpadding="5">
  <tr>
  %s
  </tr>
  </table>
</form>
<div>
"""
NAME_LINK = '<class="buttons"><input type="hidden" name="form_id" value="903438" /><br><input id="view" class="submitLink" type="submit" name="view" value="'
NAME_LINK2 = '" />'
BEGIN = '<tr>'
START_ITEM_HTML = '<td>'
END_ITEM_HTML = '</td>'

ALL_STREAMS_HTML = """
<div id="article">
<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-right: solid 1px; border-left: solid 1px; border-top: none; border-bottom: none; border-width:1px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}
</style>
<table>
%s
</table>
<div>
"""

def olderthanhour(checktimestring):
  hourago = datetime.now() - timedelta(minutes=30)
  if(checktimestring < str(hourago)):
    logging.info("checktimestring: " + str(checktimestring) + " hour ago: " + str(hourago))
    logging.info("returning true")
    return True
  else:
    logging.info("checktimestring: " + str(checktimestring) + " hour ago: " + str(hourago))
    logging.info("returning false")
    return False

def generateallimagelinks(urllist,streamnamelist):
  BEGIN_ROW = '<tr>'
  BEGIN_LINK = '<th class="tg-031e"><class="buttons"><input id ="StreamsLink" input type="image" src="'
  LINK2 = '" width=250 height=225 name="Streamname" value="'
  LINK3 = '"/><br><input id="Label" name="Label" type="text" readonly="readonly" value="'
  END_LINK = '"></th>'
  END_ROW = '</tr>'

  htmlstringfinal = ""
  length = len(urllist)
  lengthstreams = len(streamnamelist)
  fullrow = length/3
  partrow = length%3
  ispartrow = 0
  if not partrow == 0:
    ispartrow = 1
  iternum = 0
  for x in range(0,(fullrow + ispartrow)):
    htmlstringfinal = htmlstringfinal + BEGIN_ROW
    if x < fullrow:
      for y in range(0,3):
        htmlstringfinal = htmlstringfinal + BEGIN_LINK + urllist[iternum] + LINK2 + streamnamelist[iternum] + LINK3 + streamnamelist[iternum] + END_LINK
        iternum = iternum + 1
      htmlstringfinal = htmlstringfinal + END_ROW
    else:
      for y in range(0,partrow):
        htmlstringfinal = htmlstringfinal + BEGIN_LINK + urllist[iternum] + LINK2 + streamnamelist[iternum] + LINK3 + streamnamelist[iternum] + END_LINK
        iternum = iternum + 1
      htmlstringfinal = htmlstringfinal + END_ROW
  return htmlstringfinal


def generateimagelinks(urllist):
  BEGIN = '<th class="tg-031e"><img src="'
  END = '" alt="Image Unavailable" width="250" height="225"></th>'
  htmlstringfinal = ""
  length = len(urllist)
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + urllist[x] + END
  return htmlstringfinal



def generatestreamsiownlist(updatelist):
  START_CHECKBOX = '<td><input id="own" name="own" class="element checkbox" type="checkbox" value="'
  END_CHECKBOX = '" /></td></tr>'
  htmlstringfinal = ""
  length = len(updatelist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + NAME_LINK + updatelist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML + START_ITEM_HTML+ updatelist['dates'][x] + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['imagenums'][x]) + END_ITEM_HTML
    htmlstringfinal = htmlstringfinal + START_CHECKBOX + updatelist['streamnames'][x] + END_CHECKBOX
  return htmlstringfinal

def generatestreamssubscribed(updatelist):
  START_CHECKBOX = '<td><input id="sub" name="sub" class="element checkbox" type="checkbox" value="'
  END_CHECKBOX = '" /></td></tr>'
  htmlstringfinal = ""
  length = len(updatelist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + NAME_LINK + updatelist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML + START_ITEM_HTML+ updatelist['dates'][x] + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['imagenums'][x]) + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['views'][x]) + END_ITEM_HTML
    htmlstringfinal = htmlstringfinal + START_CHECKBOX + updatelist['streamnames'][x] + END_CHECKBOX
  return htmlstringfinal  

def generatetrendingstreams(trendinglist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td align="center" valign="center">'
  END_ITEM_HTML = '</td>'
  START_IMG_SRC_TAG = '<img src="'
  #END_IMG_SRC_TAG = '" width="20%"/>'
  END_IMG_SRC_TAG = '" alt="Image Unavailable" width="300" height="214"/>'
  htmlstringfinal = ""
  length = 3
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + START_ITEM_HTML + START_IMG_SRC_TAG + trendinglist['image'][x] + END_IMG_SRC_TAG + "<br />" +  NAME_LINK + trendinglist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML 
  return htmlstringfinal

def generatetrendingstreamslinks(trendinglist):
  BEGIN_ROW = '<tr>'
  BEGIN_LINK = '<th class="tg-031e"><class="buttons"><input id ="StreamsLink" input type="image" src="'
  LINK2 = '" width=250 height=225 name="Streamname" value="'
  LINK3 = '"/><br><input id="Label" name="Label" type="text" readonly="readonly" value="'
  END_LINK = '"></th>'
  END_ROW = '</tr>'

  htmlstringfinal = ""
  length = 3
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN_LINK + trendinglist['image'][x] + LINK2 + trendinglist['streamnames'][x] + LINK3 + trendinglist['streamnames'][x] + END_LINK
  htmlstringfinal = htmlstringfinal + END_ROW
  return htmlstringfinal

def generatesearchedstreams(searchlist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td align="center" valign="center">'
  END_ITEM_HTML = '</td>'
  START_IMG_SRC_TAG = '<img src="'
  #END_IMG_SRC_TAG = '" width="20%"/>'
  END_IMG_SRC_TAG = '" alt="Image Unavailable" width="300" height="214"/>'
  htmlstringfinal = ""
  length = len(searchlist['streamnames'])
  for x in range(0,length):
      htmlstringfinal = htmlstringfinal + START_ITEM_HTML + START_IMG_SRC_TAG + searchlist['image'][x] + END_IMG_SRC_TAG + "<br />" + NAME_LINK + searchlist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML
  return htmlstringfinal

def generatesearchedstreamslinks(searchlist):
  BEGIN_ROW = '<tr>'
  BEGIN_LINK = '<th class="tg-031e"><class="buttons"><input id ="StreamLink" input type="image" src="'
  LINK2 = '" width=250 height=225 name="Streamname" value="'
  LINK3 = '"/><br><input id="Label" name="Label" type="text" readonly="readonly" value="'
  END_LINK = '"></th>'
  END_ROW = '</tr>'

  htmlstringfinal = ""
  lengthstreams = len(searchlist['streamnames'])
  logging.info('lengthstreams : ' + str(lengthstreams))
  fullrow = lengthstreams/3
  partrow = lengthstreams%3
  ispartrow = 0
  if not partrow == 0:
    ispartrow = 1
  iternum = 0
  for x in range(0,(fullrow + ispartrow)):
    htmlstringfinal = htmlstringfinal + BEGIN_ROW
    if x < fullrow:
      for y in range(0,3):
        if y<lengthstreams:
          htmlstringfinal = htmlstringfinal + BEGIN_LINK + searchlist['image'][iternum] + LINK2 + searchlist['streamnames'][iternum] + LINK3 + searchlist['streamnames'][iternum] + END_LINK
          iternum = iternum + 1
        htmlstringfinal = htmlstringfinal + END_ROW
    else:
      for y in range(0,partrow):
        htmlstringfinal = htmlstringfinal + BEGIN_LINK + searchlist['image'][iternum] + LINK2 + searchlist['streamnames'][iternum] + LINK3 + searchlist['streamnames'][iternum] + END_LINK
        iternum = iternum + 1
      htmlstringfinal = htmlstringfinal + END_ROW
  return htmlstringfinal


def generateallstreams(allStreamslist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td class="tg-031e">'
  END_ITEM_HTML = '</td>'
  htmlstringfinal = ""
  length = len(allStreamslist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + allStreamslist['streamnames'][x] + END_ITEM_HTML 
  return htmlstringfinal

def addcoverurl(coverurl,streamname):
  logging.info('In add coverurl for ' + str(streamname) + ' at ' + coverurl)
  coverurl[streamname] = coverurl
    

def processSubscriberList(subdata):
  #Gets valid emails from form data for subscribers
    subdata = subdata.strip()
    subdata = subdata.split(',')
    subscriberlist = list()
    for subscriber in subdata:
      subscriber = subscriber.strip()
      #TODO - For now remove check for valid email?
      if(re.match(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$',subscriber)):
        logging.info('Found valid email')
        subscriberlist.append(subscriber)
    return subscriberlist

def processTagList(tagdata):
  #Gets tags from form data, probably need better valid tag checking
  tagdata = tagdata.strip()
  tagdata = tagdata.split(',')
  taglist = list()
  for tag in tagdata:
    tag = tag.strip()
    if(re.match('^#.*',tag)):
      taglist.append(tag)
  return taglist

def create_file(filename, file, contenttype):
  logging.info('Creating file %s\n' % filename)
  write_retry_params = gcs.RetryParams(backoff_factor=1.1)
  gcs_file = gcs.open(filename,'w',content_type=contenttype,options={'x-goog-acl': 'public-read'},retry_params=write_retry_params)
  gcs_file.write(file)
  gcs_file.close()
  #TODO: don't think we'll keep these temp files...once everything is working.
  #for now used by delete_files to clean up the datastore before reloading the app
  tmp_filenames_to_clean_up.append(filename)

#temporary helper to cleanup test files written
def delete_files():
    #logging.info('Deleting files...\n' + str(tmp_filenames_to_clean_up))
    #for filename in tmp_filenames_to_clean_up:
    #  logging.info('Deleting file %s\n' % filename)
      try:
        #gcs.delete(filename)
        gcs.delete('/connexusssar.appspot.com/ColorFlag/066e0e0f-4bd7-11e4-9d1d-710007c381d9')
      except gcs.NotFoundError:
        logging.info("File not found error")
        pass

def delete_images(imagefiles):
  for filename in imagefiles:
    logging.info('Deleting image: ' + str(filename))
    try:
      gcs.delete(filename)
      #blobstore.delete(filename)
      logging.info('Finished deleting file')
    except gcs.NotFoundError:
      pass

###start upload stuff
def cleanup(blob_keys):
    blobstore.delete(blob_keys)


class UploadHandler(webapp2.RequestHandler):

    def initialize(self, request, response):
        super(UploadHandler, self).initialize(request, response)
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers[
            'Access-Control-Allow-Methods'
        ] = 'OPTIONS, HEAD, GET, POST, PUT, DELETE'
        self.response.headers[
            'Access-Control-Allow-Headers'
        ] = 'Content-Type, Content-Range, Content-Disposition'

    def validate(self, file):
        if file['size'] < MIN_FILE_SIZE:
            file['error'] = 'File is too small'
        elif file['size'] > MAX_FILE_SIZE:
            file['error'] = 'File is too big'
        elif not ACCEPT_FILE_TYPES.match(file['type']):
            file['error'] = 'Filetype not allowed'
        else:
            return True
        return False

    def get_file_size(self, file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size

    def write_blob(self, data, info):
        blob = files.blobstore.create(
            mime_type=info['type'],
            _blobinfo_uploaded_filename=info['name']
        )
        with files.open(blob, 'a') as f:
            f.write(data)
        files.finalize(blob)
        return files.blobstore.get_blob_key(blob)

    def handle_upload(self):
        logging.info('In handle upload. Self request is: ' + str(self.request))
        results = []
        blob_keys = []
        try:
            streamname = self.request.get('Streamname')
            streamname = streamname.split("'s Str")[0]
            logging.info('streamname is: ' + str(streamname))
            logging.info('Check if stream exists')
            present_query = Stream.query(Stream.streamname == streamname)
            existsstream = present_query.get()
            logging.info('Query returned: ' + str(existsstream))
            if not existsstream == None:
              comments = self.request.get('comments')
              try:
                logging.info("Headers is: " + str(self.request.headers))
                latlong = self.request.headers['X-Appengine-Citylatlong']
                coord = latlong.split(',')
                latitude = float(coord[0])
                longitude = float(coord[1])
                logging.info("latitude: " + str(latitude))
                logging.info("longitude: " + str(longitude))
              except:
                logging.info("Couldn't get location, defaulting to pflugerville tx")
                latitude = 30.439370
                longitude = -97.620004
              creationdate = str(datetime.now().date())
              imageid = str(uuid.uuid1())
              bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
              logging.info("My bucket name is: " + str(bucket_name))
              bucket = '/' + bucket_name
              filename = bucket + '/' + streamname + '/' + imageid
              for name, fieldStorage in self.request.POST.items():
                if type(fieldStorage) is unicode:
                  continue
                result = {}
            #result is name, type, size
            # Save filename to result array
                result['name'] = re.sub(
                    r'^.*\\',
                    '',
                    fieldStorage.filename
                ) 
                logging.info("Filename is: " + str(result['name']))
                result['type'] = fieldStorage.type
                logging.info("Content type is: " + str(result['type']))
                result['size'] = self.get_file_size(fieldStorage.file)
                if self.validate(result):
                #write to cloud storage
                #blob_key = str(
                 #   self.write_blob(fieldStorage.value, result))
            # Create a GCS file with GCS client.
                  with gcs.open(filename, 'w') as f:
                      f.write(fieldStorage.value)
            # Blobstore API requires extra /gs to distinguish against blobstore files.
                  blobstore_filename = '/gs' + filename
                  blob_key = blobstore.create_gs_key(blobstore_filename)
                  logging.info("write file to cloud storage and store url in stream")
                  logging.info('Maybe append urls to delete')
                  blob_keys.append(blob_key)
                  result['deleteType'] = 'DELETE'
                  logging.info("Host URL: " + str(self.request.host_url))
                  logging.info("secure host URL: " + str(self.request.host_url.startswith('https')))
                  result['deleteUrl'] = self.request.host_url + '/UploadHandler' +\
                      '?key=' + urllib.quote(blob_key, '')
                  if (IMAGE_TYPES.match(result['type'])):
                      try:
                          result['url'] = images.get_serving_url(
                              blob_key,
                          )
                          result['thumbnailUrl'] = result['url'] +\
                              THUMBNAIL_MODIFICATOR
                          logging.info("Thumbnail url is: " + str(result['thumbnailUrl']))
                          myimage = Image(parent=ndb.Key('connexusssar', 'connexusssar'))
                          myimage.imageid = imageid
                          myimage.imagefilename = result['name']
                          myimage.comments = comments
                          myimage.imagefileurl = result['url']
                          myimage.imagecreationdate = creationdate
                          myimage.imagelatitude = latitude
                          myimage.imagelongitude = longitude
                          myimage.imagestreamname = streamname
                          myimage.put()
                          logging.info('Saved this image to images')
                          thisimagelist = existsstream.imagelist
                          thisimagelist.append(myimage)
                          existsstream.imagelist = thisimagelist
                          existsstream.put()
                      except:  
                          # Could not get an image serving url
                          logging.info('Could not get an image serving Url')
                          pass
                  if not 'url' in result:
                      result['url'] = self.request.host_url +\
                          '/' + blob_key + '/' + urllib.quote(
                              result['name'].encode('utf-8'), '')
                      logging.info("Result URL is: " + str(result['url']))
              results.append(result)
        except:
            logging.info("exception uploading files")
        return results

    def options(self):
        pass

    def head(self):
        pass

    def get(self):
        pass

    def post(self):
        if (self.request.get('_method') == 'DELETE'):
            logging.info("Got a delete")
            return self.delete()
        logging.info("Post request: " + str(self.request))
        result = {'files': self.handle_upload()}
        logging.info("Post result: " + str(result))
        s = json.dumps(result, separators=(',', ':'))
        redirect = self.request.get('redirect')
        if redirect:
            logging.info("redirecting after post and result from handle upload")
            return self.redirect(str(
                redirect.replace('%s', urllib.quote(s, ''), 1)
            ))
        if 'application/json' in self.request.headers.get('Accept'):
            self.response.headers['Content-Type'] = 'application/json'
        logging.info("Post result writing is: " + str(s))
        self.response.write(s)

    def delete(self):
        logging.info(str(self.request))
        logging.info("Need to delete files from cloud and images")
        key = self.request.get('key') or ''
        thisurl = images.get_serving_url(key)
        logging.info("url to search: " + str(thisurl))
        deleteimage_query = Image.query(Image.imagefileurl == thisurl)
        deleteimage = deleteimage_query.get()
        logging.info('Query returned: ' + str(deleteimage))
        deleteimagestream = deleteimage.imagestreamname
        logging.info("Delete stream: " + str(deleteimagestream))
        present_query = Stream.query(Stream.streamname == deleteimagestream)
        existsstream = present_query.get()
        logging.info("Stream found: " + str(existsstream))
        imagelist = existsstream.imagelist
        for myimage in imagelist:
          if myimage.imagefileurl == thisurl:
            logging.info("Removing myimage: " + str(myimage))
            imagelist.remove(myimage)
            break
        logging.info("updated imagelist: " + str(imagelist))
        deleteimagekey = deleteimage.key
        deleteimagekey.delete()
        existsstream.imagelist = imagelist
        logging.info('Updated imagelist writing back: ' + str(imagelist))
        existsstream.put()
        logging.info('Query returned: ' + str(existsstream))        
        blobstore.delete(key)
        s = json.dumps({key: True}, separators=(',', ':'))
        if 'application/json' in self.request.headers.get('Accept'):
            self.response.headers['Content-Type'] = 'application/json'
        logging.info('Result json from delete: ' + str(s))
        self.response.write(s) 


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, key, filename):
        if not blobstore.get(key):
            self.error(404)
        else:
            # Prevent browsers from MIME-sniffing the content-type:
            self.response.headers['X-Content-Type-Options'] = 'nosniff'
            # Cache for the expiration time:
            self.response.headers['Cache-Control'] = 'public,max-age=%d' % EXPIRATION_TIME
            # Send the file forcing a download dialog:
            self.send_blob(key, save_as=filename, content_type='application/octet-stream')

###end file upload code

class GetAllImages(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    logging.info("In Get all images: Current user is: " + str(user))
    creationdatelist = list()
    imageurllist = list()
    imagelatitudelist = list()
    imagelongitudelist = list()
    allimagesquery = Image.query(Image.imagefileurl != "")
    allimages = allimagesquery.fetch()
    for thisimage in allimages:
      logging.info("This image is: " + str(thisimage))
      imageurllist.append(thisimage.imagefileurl)
      creationdatelist.append(thisimage.imagecreationdate)
      imagelatitudelist.append(thisimage.imagelatitude)
      imagelongitudelist.append(thisimage.imagelongitude)
    logging.info("All images is: " + str(allimages))
    data = json.dumps({"id":1,"content":"Hello, World!","imageurllist":imageurllist,"creationdatelist":creationdatelist,"imagelatitudelist":imagelatitudelist,"imagelongitudelist":imagelongitudelist})
    logging.info("Data writing: " + str(data))
    self.response.write(data)

class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    logging.info("Current user is: " + str(user))
    template = JINJA_ENVIRONMENT.get_template('index.html')
    template2 = JINJA_ENVIRONMENT.get_template('mappage.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : ""}
    if user:
      fullhtml = template.render(templateVars) + template2.render()
      self.response.write(fullhtml)
    else:
      self.redirect(users.create_login_url(self.request.uri))

class Map(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    if user:
      fullhtml = template.render(templateVars)
      self.response.write(fullhtml)
    else:
      self.redirect(users.create_login_url(self.request.uri))

class ViewPageHandler(webapp2.RequestHandler):
  def post(self):
    logging.info('Test View page handler:')
    try:
      streamname = self.request.get('Streamname')
      logging.info("Request: " + str(self.request))
      streamname = streamname.split("'s Str")[0]
      logging.info("Streamname is: " + str(streamname))
      oldpagerange = self.request.get('Pagerange')
      temp1 = oldpagerange.split('Showing images: [')[1]
      temp2 = temp1.split('-')
      start = temp2[0]
      end = temp2[1].split(']')[0]
      morepics = self.request.get('More_Pictures')
      logging.info('Morepics is: ' + str(morepics))
      upload = self.request.get('Upload')
      logging.info('Upload is: ' + str(upload))
      subscribe = self.request.get('Subscribe')
      logging.info("Subscribe is: " + str(subscribe))
      imagelinks = ""
      if (str(upload) == 'Upload'):
        logging.info('Got into upload?')
        try:
          imagefile = self.request.get('files[]')
          logging.info("single is: " + str(imagefile))
          files = self.request.POST.multi.__dict__['_items']
          logging.info("multi is " + str(files))
          for afile in files:
            logging.info("Afile is: " + str(afile))
            logging.info("Type is : " + str(type(afile)))
            if afile[0] == 'files[]':
              filename = afile[1].filename
              imagefile = afile[1].value
              logging.info(str(imagefile))
          #filename = self.request.params["files[]"].filename 
              picdata = imagefile.encode("base64")
              logging.info("filename: " + str(filename))
              (name,extension) = os.path.splitext(filename)
              logging.info("extention: " + str(extension))
              contenttype = ""
              extension = extension.lower()
              if extension == '.gif':
                contenttype = 'image/gif'
              elif extension == '.jpg':
                contenttype = 'image/jpeg'
              elif extension == '.png':
                contenttype = 'image/png'
              else:
                contenttype = None
              logging.info("Content type is: " + str(contenttype))
              if not contenttype == None:
                comments = self.request.get('Comments')
              mydata = json.dumps({"uploadimage": picdata, "streamname": streamname, "contenttype": contenttype, "comments": comments, "filename": filename})
              url = 'http://' + AP_ID_GLOBAL + '/UploadImage'
              result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
              logging.info("upload image result: " + str(result.content))
        except:
          logging.info("No file selected error")
        else:
          logging.info('Unrecognized image type.')
        self.redirect('/MgmtPage')
      elif (str(subscribe) == 'Subscribe'):
        logging.info("Subscribe is: " + str(subscribe))
        user = users.get_current_user()
        user = str(user.email())
        mydata = json.dumps({"subuser": user, "streamname": streamname})
        url = 'http://' + AP_ID_GLOBAL + '/SubscribeStream'
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
        self.redirect('/MgmtPage')
      elif (str(morepics) == 'More Pictures'):
        logging.info('View more pictures...TODO')
        newend = int(end)
        newstart = int(start)
        if ((int(end)-int(start)) >= 2):
          newstart = int(start) + 3
          newend = int(end) + 3
        else:
          newend = 2
          newstart = 0
        mydata = json.dumps({"pagerange": [newstart,newend], "streamname": streamname})
        logging.info(str(mydata))
        url = 'http://' + AP_ID_GLOBAL + '/ViewStream'
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
        jsonresult = json.loads(result.content)
        if jsonresult['pagerange'] == list():
          logging.info("That range gave back an empty list, starting at beginning of stream")
          mydata = json.dumps({"pagerange": [0,2], "streamname": streamname})
          url = 'http://' + AP_ID_GLOBAL + '/ViewStream'
          result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30) 
          jsonresult = json.loads(result.content)
          if jsonresult['pagerange'] == list():
            newstart = 0
            newend = 0
          else:
            newstart = jsonresult['pagerange'][0]
            newend = jsonresult['pagerange'][1]
            imagelinks = generateimagelinks(jsonresult['picurls'])                
        else:
          newstart = jsonresult['pagerange'][0]
          newend = jsonresult['pagerange'][1]
          imagelinks = generateimagelinks(jsonresult['picurls']) 
        template = JINJA_ENVIRONMENT.get_template('index.html')
        template2 = JINJA_ENVIRONMENT.get_template('viewstreampage.html')
        templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
        templateVars2 = {"streamname":str(streamname),"picturelist":imagelinks, "rangestart":str(newstart),"rangeend":str(newend)}
        #fullhtml = template.render(templateVars) + (VIEW_STREAM_HTML % (str(streamname),imagelinks,str(newstart),str(newend)))
        fullhtml = template.render(templateVars) + template2.render(templateVars2)
        self.response.write(fullhtml)
    except:
      logging.info("Problem uploading file")
      self.redirect('/Error')

class Image(ndb.Model):
  imageid = ndb.StringProperty()
  imagefilename = ndb.StringProperty()
  comments = ndb.StringProperty()
  imagefileurl = ndb.StringProperty()
  imagecreationdate = ndb.StringProperty()
  imagestreamname = ndb.StringProperty()
  imagelatitude = ndb.FloatProperty()
  imagelongitude = ndb.FloatProperty()

class Stream(ndb.Model):
  streamname = ndb.StringProperty(indexed=True)
  creationdate = ndb.StringProperty()
  viewdatelist = ndb.StringProperty(repeated=True)
  viewdatelistlength = ndb.IntegerProperty()
  owner = ndb.StringProperty()
  submessage = ndb.StringProperty()
  streamsubscribers = ndb.StringProperty(repeated=True)
  taglist = ndb.StringProperty(indexed=False,repeated=True)
  coverurl = ndb.StringProperty(indexed=False)
  commentlist = ndb.StringProperty(indexed=False,repeated=True) 
  imagelist = ndb.StructuredProperty(Image,repeated=True)

class MgmtPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      user = user.email()
    else:
      self.redirect(users.create_login_url(self.request.uri))
    logging.info("Current user is: " + user)
    mydata = json.dumps({'userid':user})
    url = 'http://' + AP_ID_GLOBAL + '/ManageStream'
    result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
    logging.info('Result is: ' + str(result.content))
    resultobj = json.loads(result.content)
    streamsiown = resultobj['streamlist']
    streamsisubscribe = resultobj['subscribedstreamlist']
    #get the list of streamnames I own:
    myupdatelist = {'streamnames':list(),'dates':list(),'imagenums':list()}
    myupdatelist2 = {'streamnames':list(),'dates':list(),'views':list(),'imagenums':list()}
    for ownstreams in streamsiown:
      name = ownstreams['streamname']
      imagelist = ownstreams['imagelist']
      numpics = len(imagelist)
      if len(imagelist) == 0:
        lastnewpicdate = 'N/A'
      else:
        lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
      myupdatelist['streamnames'].append(name)
      myupdatelist['dates'].append(lastnewpicdate)
      myupdatelist['imagenums'].append(numpics)
    logging.info('My update list to generate html rows: ' + str(myupdatelist))
    for ownstreams in streamsisubscribe:
      name = ownstreams['streamname']
      imagelist = ownstreams['imagelist']
      numpics = len(imagelist)
      if len(imagelist) == 0:
        lastnewpicdate = 'N/A'
      else:
        lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
      myviews = ownstreams['viewdatelistlength']
      myupdatelist2['streamnames'].append(name)
      myupdatelist2['dates'].append(lastnewpicdate)
      myupdatelist2['views'].append(myviews)
      myupdatelist2['imagenums'].append(numpics)
    logging.info('My update list to generate html rows: ' + str(myupdatelist2))
    mystreamshtml = generatestreamsiownlist(myupdatelist)
    mysubscribeshtml = generatestreamssubscribed(myupdatelist2)
    if user:
      template = JINJA_ENVIRONMENT.get_template('index.html')
      templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
      template2 = JINJA_ENVIRONMENT.get_template('mgmtpage.html')
      templateVars2 = { "streamsown" : mystreamshtml, "streamssubscribe" : mysubscribeshtml }
      fullhtml = template.render(templateVars) + template2.render(templateVars2)
      self.response.write(fullhtml)
    else:
      self.redirect(users.create_login_url(self.request.uri))

class CreatePage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    logging.info("Current user is: " + str(user))
    if user:
      template = JINJA_ENVIRONMENT.get_template('index.html')
      templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
      createtemplate = JINJA_ENVIRONMENT.get_template('createpage.html')
      fullhtml = template.render(templateVars) + createtemplate.render()
      self.response.write(fullhtml)
    else:
      self.redirect(users.create_login_url(self.request.uri))


class ViewPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    fullhtml = template.render(templateVars) + "<br><br><br> View page does not support HTTP get.</body></html>"
    self.response.write(fullhtml)

  def post(self):
      BAD_SCRIPT = """<script id="template-upload" type="text/x-tmpl">
{% for (var i=0, file; file=o.files[i]; i++) { %}
    <tr class="template-upload fade">
        <td>
            <span class="preview"></span>
        </td>
        <td>
            <p class="name">{%=file.name%}</p>
            <strong class="error text-danger"></strong>
        </td>
        <td>
            <p class="size">Processing...</p>
            <div class="progress progress-striped active" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="progress-bar progress-bar-success" style="width:0%;"></div></div>
        </td>
        <td>
            {% if (!i && !o.options.autoUpload) { %}
                <button class="btn btn-primary start" disabled>
                    <i class="glyphicon glyphicon-upload"></i>
                    <span>Start</span>
                </button>
            {% } %}
            {% if (!i) { %}
                <button class="btn btn-warning cancel">
                    <i class="glyphicon glyphicon-ban-circle"></i>
                    <span>Cancel</span>
                </button>
            {% } %}
        </td>
    </tr>
{% } %}
</script>
<!-- The template to display files available for download -->
<script id="template-download" type="text/x-tmpl">
{% for (var i=0, file; file=o.files[i]; i++) { %}
    <tr class="template-download fade">
        <td>
            <span class="preview">
                {% if (file.thumbnailUrl) { %}
                    <a href="{%=file.url%}" title="{%=file.name%}" download="{%=file.name%}" data-gallery><img src="{%=file.thumbnailUrl%}"></a>
                {% } %}
            </span>
        </td>
        <td>
            <p class="name">
                {% if (file.url) { %}
                    <a href="{%=file.url%}" title="{%=file.name%}" download="{%=file.name%}" {%=file.thumbnailUrl?'data-gallery':''%}>{%=file.name%}</a>
                {% } else { %}
                    <span>{%=file.name%}</span>
                {% } %}
            </p>
            {% if (file.error) { %}
                <div><span class="label label-danger">Error</span> {%=file.error%}</div>
            {% } %}
        </td>
        <td>
            <span class="size">{%=o.formatFileSize(file.size)%}</span>
        </td>
        <td>
            {% if (file.deleteUrl) { %}
                <button class="btn btn-danger delete" data-type="{%=file.deleteType%}" data-url="{%=file.deleteUrl%}"{% if (file.deleteWithCredentials) { %} data-xhr-fields='{"withCredentials":true}'{% } %}>
                    <i class="glyphicon glyphicon-trash"></i>
                    <span>Delete</span>
                </button>
                <input type="checkbox" name="delete" value="1" class="toggle">
            {% } else { %}
                <button class="btn btn-warning cancel">
                    <i class="glyphicon glyphicon-ban-circle"></i>
                    <span>Cancel</span>
                </button>
            {% } %}
        </td>
    </tr>
{% } %}
</script>"""
      data = json.loads(self.request.body)
      logging.info('Json data sent to this function: ' + str(data))
      streamname = data['streamname']
      pagerange = data['pagerange']
      logging.info('Pagerange: ' + str(pagerange))
      start = int(pagerange[0])
      end = int(pagerange[1])
      logging.info('Start is: ' + str(start) + ' End is: ' + str(end))
      url = 'http://' + AP_ID_GLOBAL + '/ViewStream'
      mydata = json.dumps({'streamname':streamname,'pagerange':[start,end]})
      result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
      jsonresult = json.loads(result.content)
      imagelinks = generateimagelinks(jsonresult['picurls'])
      logging.info("ViewStream call result: " + str(result.content))
      template = JINJA_ENVIRONMENT.get_template('index.html')
      template2 = JINJA_ENVIRONMENT.get_template('viewstreampage.html')
      templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
      templateVars2 = {"streamname":str(streamname),"badscript": BAD_SCRIPT, "picturelist":imagelinks, "rangestart":str(pagerange[0]),"rangeend":str(pagerange[1])}
      fullhtml = template.render(templateVars) + template2.render(templateVars2)
      self.response.write(fullhtml)

class SearchPage(webapp2.RequestHandler):
  def get(self):
    #Retrieve top 3 trending streams
    url = 'http://' + AP_ID_GLOBAL + '/SearchStreams'
    logging.info('request: ' + str(self.request))
    searchString = self.request.get('searchString')
    logging.info('searchString is :' + searchString)
    template = JINJA_ENVIRONMENT.get_template('index.html')   
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }    
    fullhtml = template.render(templateVars)

    try:
      if searchString == "":
        logging.info('searchString is null')
        fullhtml = template.render(templateVars) + SEARCH_STREAMS_HTML + "</body></html>"
        #fullhtml = (S_HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + SEARCH_STREAMS_HTML + "</body></html>"
        #self.response.write(fullhtml)
      else:
        logging.info('searchString is not null')
        searchParams = json.dumps({'streamname':searchString})
        logging.info('URL for SearchStreams is : ' + str(url))
        result = urlfetch.fetch(url=url, payload=searchParams, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
        logging.info('SearchStreams Result is: ' + str(result.content))
        if not (str(result.content) == "{'errorcode':6}"):
          searchedStreams = json.loads(result.content)
          #searchedStreams = resultobj['mostviewedstreams']
          logging.info('SearchStreams from service: ' + str(searchedStreams))

          searchedStreamsResult = {'streamnames':list(),'imagenums':list(), 'image':list()}
          for tstream in searchedStreams:
            imgstring =""
            name = tstream['streamname']
            logging.info("Sreached stream : " + str(name))
            imagelist = tstream['imagelist']
            logging.info("Searched stream image list : " + str(imagelist))
            numpics = len(imagelist)
            logging.info('This stream imagelist: ' + str(numpics))
            if len(imagelist) == 0:
              lastnewpicdate = 'N/A'
              imgString = ""
            else:
              lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
              imgString = imagelist[0]['imagefileurl']
              logging.info('image URL is : ' + str(imgString))
            logging.info("Sreached stream creation date : " + lastnewpicdate)

            searchedStreamsResult['streamnames'].append(name)
            searchedStreamsResult['imagenums'].append(numpics)
            searchedStreamsResult['image'].append(imgString)
          logging.info('Search returned following Streams :' + str(searchedStreamsResult))
          #searchStreamHtml = generatesearchedstreams(searchedStreamsResult)
          searchStreamHtml = generatesearchedstreamslinks(searchedStreamsResult)
          logging.info('Search stream page html: ' + searchStreamHtml)
          length = len(searchedStreamsResult['streamnames'])
          searchMsg = "<p id='Label'>" + str(length) + " results for " + str(searchString) + ", click on an image to view stream </p>"
          #fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + SEARCH_STREAMS_HTML + searchMsg + (SEARCH_RESULT_HTML % (searchStreamHtml)) + "</body></html>"
          #self.response.write(fullhtml)
          fullhtml = template.render(templateVars) + SEARCH_STREAMS_HTML + searchMsg + (SEARCH_RESULT_HTML % (searchStreamHtml)) + "</body></html>"
        else:
          searchMsg = "<p> An Error occurred while searching for streams. Try again. </p>"
          #fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + SEARCH_STREAMS_HTML + searchMsg + (SEARCH_RESULT_HTML % (searchStreamHtml)) + "</body></html>"
          #self.response.write(fullhtml)
          fullhtml = template.render(templateVars) + SEARCH_STREAMS_HTML + searchMsg + (SEARCH_RESULT_HTML % (searchStreamHtml)) + "</body></html>"
    except:
      searchMsg = "<p> An Error occurred while searching for streams. Try again. </p>"
      #fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + SEARCH_STREAMS_HTML + searchMsg + "</body></html>"
      fullhtml = template.render(templateVars) + SEARCH_STREAMS_HTML + searchMsg + "</body></html>"
    self.response.write(fullhtml)



class TrendingPage(webapp2.RequestHandler):
  def get(self):
    logging.info('request :' + str(self.request))
    global cron_rate
    cronRateStr = self.request.get('cronRate')
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    if cronRateStr == "":
      logging.info("No Cron rate was selected")
    else:
      logging.info('Cron rate selected : ' + str(cronRateStr))
      if cronRateStr == 'Five':
        cron_rate = 5
      elif cronRateStr== 'Hour': 
        cron_rate = 60
      elif cronRateStr == 'Day':
        cron_rate = 1440
      elif cronRateStr == 'No':
        cron_rate = -1
      logging.info("Cron Rate is now %d." % cron_rate)

    streamname = cgi.escape(self.request.get('Streamname'))
    if streamname != "":
      logging.info("Request "  + str(self.request))
      url = 'http://' + AP_ID_GLOBAL + '/ViewPage'
      mydata = json.dumps({'streamname':str(streamname),'pagerange':[0,2]})
      result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
      self.response.write(str(result.content))
    else: 
      #Retrieve top 3 trending streams
      url = 'http://' + AP_ID_GLOBAL + '/GetMostViewedStreams'
      params = json.dumps({})
      logging.info('URL for GetMostViewedStreams is : ' + str(url))
      result = urlfetch.fetch(url=url, payload=params, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
      
      if result == None:
        searchMsg = "<p> No trending reports were found. </p>"
        fullhtml = template.render(templateVars) + TRENDING_PAGE_STYLE + searchMsg + TRENDING_REPORT_HTML + "</body></html>"
      else:
        logging.info('GetMostViewedStreams Result is: ' + str(result.content))
        resultobj = json.loads(result.content)
        trendingStreams = resultobj['mostviewedstreams']
        logging.info('TrendingStreams from service: ' + str(trendingStreams))

        #get list of top three streams
        trendingStreamsResult = {'streamnames':list(),'imagenums':list(), 'image':list()}
        for tstream in trendingStreams:
          imageURL = ""
          logging.info('tstream : ' + str(tstream))
          name = tstream['streamname']
          logging.info("Trending stream : " + str(name))
          imagelist = tstream['imagelist']
          logging.info("Trending stream image list : " + str(imagelist))
          numpics = len(imagelist)
          logging.info('This stream imagelist: ' + str(numpics))
          if len(imagelist) == 0:
            lastnewpicdate = 'N/A'
          else:
            lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
            imageURL = imagelist[0]['imagefileurl']
          logging.info("Treading stream creation date : " + lastnewpicdate)

          trendingStreamsResult['streamnames'].append(name)
          trendingStreamsResult['imagenums'].append(numpics)
          trendingStreamsResult['image'].append(imageURL)
        logging.info('Top Three Trending Streams :' + str(trendingStreamsResult))
        #trendingStreamHtml = generatetrendingstreams(trendingStreamsResult)
        trendingStreamHtml = generatetrendingstreamslinks(trendingStreamsResult)
        logging.info('Trending Stream table html :' + str(trendingStreamHtml))

        fullhtml = template.render(templateVars) + TRENDING_PAGE_STYLE + (TRENDING_STREAMS_HTML % (trendingStreamHtml)) + TRENDING_REPORT_HTML + "</body></html>"
        #logging.info("HTML Page: " + fullhtml)
      self.response.write(fullhtml)

class SocialPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    fullhtml = template.render(templateVars) + "<br><br><br> Social page coming soon</body></html>"
    self.response.write(fullhtml)

class ErrorPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    fullhtml = template.render(templateVars) + "<br><br><br> Error: you tried to create a new stream whose name is the same as an existing stream, operation did not complete.</body></html>"
    self.response.write(fullhtml)

class ViewAllStreamsPage(webapp2.RequestHandler):
  def get(self):
    url = 'http://' + AP_ID_GLOBAL + '/ViewAllStreams'
    logging.info('URL is: ' + str(url))
    payload = {'test':0}
    mydata = json.dumps(payload)
    result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
    resultjson = json.loads(result.content)
    urllist = resultjson['coverurls']
    streamnames = resultjson['streamlist']
    allimageshtml = generateallimagelinks(urllist,streamnames)
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    fullhtml = template.render(templateVars) + (VIEW_ALL_STREAM_HTML % allimageshtml)
    self.response.write(fullhtml)

#Sample function, we may not use
class GCSHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Got to GCS Handler.")
    self.response.headers['Content-Type'] = 'text/plain'
    gcs_filename = '/' + AP_ID_GLOBAL+'/gcs_demo'
    blob_key = CreateFile(gcs_filename)
    # Fetch data.
    writestring = 'Fetched data ' + str(blobstore.fetch_data(blob_key, 0, 2)) + '\n'
    self.response.write(writestring)
    # Delete files.
    blobstore.delete(blob_key)

#Sample code - not currently used, will see if needed.
class GCSServingHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
    blob_key = CreateFile('/' + AP_ID_GLOBAL + '/blobstore_serving_demo')
    self.send_blob(blob_key)


#sample code we may not
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    logging.info("Got to serveHandler.")
    resource = str(urllib.unquote(resource))
    logging.info("Resource is: " + resource)
    blob_info = blobstore.BlobInfo.get(resource)
    logging.info('Blob info is: ' + str(blob_info))
    self.send_blob(blob_info)

class Login(webapp2.RequestHandler):

  def post(self):
    login = cgi.escape(self.request.get('login_name'))
    password = cgi.escape(self.request.get('password'))
    logging.info("Login is: " + str(login))
    logging.info("password is: " + str(password))


class GetStreamData(webapp2.RequestHandler):
  #Gets create stream data from the HTML page
  #Creats the json object with the streamname, subscriber emails, and tags
  #and call Create stream web service and send the json data
   def post(self):
        user  = users.get_current_user()
        user = str(user.email())
        logging.info('Current user: ' + str(user))
        streamname = cgi.escape(self.request.get('streamname'))
        logging.info('Stream Name: ' + str(streamname))
        submessage = cgi.escape(self.request.get('submessage'))
        logging.info('Subdata: ' + str(submessage))
        subscriberdata = cgi.escape(self.request.get('subscribers'))
        logging.info('Subscriber Data: ' + str(subscriberdata))
        subscriberlist = processSubscriberList(subscriberdata)
        tagdata = cgi.escape(self.request.get('tags'))
        logging.info('Tag Data: ' + str(tagdata))
        taglist = processTagList(tagdata) 
        coverurl = cgi.escape(self.request.get('coverurl'))
        self.response.write('<html><body>Processed stream info: <pre>')
        self.response.write('<br>')
        self.response.write('Stream name: ' + str(streamname))
        self.response.write('<br>')
        self.response.write('Subscriber list: <br>')
        for subscriber in subscriberlist:
          self.response.write(subscriber)
          self.response.write('<br>')
        self.response.write('Cover url: ' + str(coverurl))
        self.response.write('Tags: ' + str(tagdata))
        self.response.write('</pre></body></html>')
        prejson = {'streamname':streamname,'subscribers':subscriberlist,'tags':taglist,'submessage':submessage,'coverurl':coverurl,'currentuser':str(user)}
        mydata = json.dumps(prejson)
        logging.info('JSON data: ' + str(mydata))
        url = 'http://' + AP_ID_GLOBAL + '/CreateStream'
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
        logging.info("Create stream call result: " + str(result.content))
        self.redirect('/MgmtPage')


class CreateStream(webapp2.RequestHandler):
  def post(self):
    try:
      data = json.loads(self.request.body)
      logging.info('Json data sent to this function: ' + str(data))

      streamname = data['streamname']
      logging.info('\nStreamname: ' + streamname)
      owner = data['currentuser']
      logging.info('\nOwner: ' + str(owner))
      if streamname == '':
        logging.info('Streamname is equal to empty string, we should exit.')
        payload = {'errorcode':3}
        result = json.dumps(payload)
        self.response.write(result)
        return 
      if owner == '':
        logging.info('Owner is equal to empty string, we should exit.')
        payload = {'errorcode':2}
        result = json.dumps(payload)
        self.response.write(result)
        return        
      #TODO: Check that streamname doens't aready exist
      logging.info('Check if stream exists')
      present_query = Stream.query(Stream.streamname == streamname)
      try:
        existsstream = present_query.get()
        logging.info('Query returned: ' + str(existsstream))
        if existsstream == None:
          alreadypresent = False
        else:
          logging.info('Setting already present to True')
          alreadypresent = True
          payload = {'errorcode':1}
      except:
        logging.info('exception occurred, set already present to True to skip create')
        alreadypresent = True
        payload = {'errorcode':3}


      if not alreadypresent:
        stream = Stream(parent=ndb.Key('connexusssar', 'connexusssar'))
        stream.streamname = streamname

        creationdate = str(datetime.now().date())
        stream.creationdate = creationdate
        logging.info('\nCreation date: ' + str(creationdate))

        viewdatelist = list()
        stream.viewdatelist = viewdatelist
        logging.info('\nViewdatelist: ' + str(viewdatelist))

        stream.viewdatelistlength = 0

        stream.owner = owner

        streamsubscribers = data['subscribers']
        stream.streamsubscribers = streamsubscribers
        logging.info('\nstreamsubscribers: ' + str(streamsubscribers))

        submessage = data['submessage']
        stream.submessage = submessage
        logging.info('\nsubmessage: ' + str(submessage))

        taglist = data ['tags']
        stream.taglist = taglist
        logging.info('\nTaglist: ' + str(taglist))

        coverurl = data['coverurl']
        stream.coverurl = coverurl
        logging.info('\nCoverurl: ' + str(coverurl))

        commentlist = list()
        stream.commentlist = commentlist
        logging.info('\nCommentlist: ' + str(commentlist))

        imagelist = list()
        stream.imagelist = imagelist
        logging.info('\nImagelist: ' + str(imagelist))
        
        stream.put()
        payload = {'errorcode':0}

    except:
      payload = {'errorcode':3}
    result = json.dumps(payload)
    self.response.write(result)

#We are probably not going to use this service, just started testing blobstore with it..
class ChooseImage(webapp2.RequestHandler):
  def get(self):
    upload_url = blobstore.create_upload_url('/upload')
    self.response.out.write('<html><body>')
    logging.info('The upload URL is: ' + str(upload_url))
    urlhtml = '<form action="' + upload_url + '" method="post" enctype="multipart/form-data">'
    logging.info('URL HTML: ' + urlhtml)
    self.response.out.write(urlhtml)
    self.response.out.write('Upload File: <input type="file" name="file"><br> <input type="submit" name="submit" value="Submit"> </form></body></html>')

#takes a user as json input, and returns the list of streams the user owns and is subscribed to
class ManageStream(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('Json data from call: ' + str(data))
    userid = data['userid']
    logging.info('Userid: ' + str(userid))

    #TODO: loop through all streams for sort and find all streams for this owner
    thisuserstreams = list()
    thisusersubscriptionlist = list()
    logging.info("Starting fetch streams owned by for: " + str(userid))
    stream_query = Stream.query(Stream.owner == userid)
    rawuserstreams = stream_query.fetch()

    for thisstream in rawuserstreams:
      thisimagelist = thisstream.imagelist
      newimagelist = list()
      for image in thisimagelist:
        currentimage = {'imageid':image.imageid,'imagefilename':image.imagefilename,'comments':image.comments,'imagecreationdate':image.imagecreationdate,'imagefileurl':image.imagefileurl}
        newimagelist.append(currentimage)
      currentstream = {'streamname':thisstream.streamname,'creationdate':thisstream.creationdate,'viewdatelist':thisstream.viewdatelist,'viewdatelistlength':thisstream.viewdatelistlength,'owner':thisstream.owner,'subscribers':thisstream.streamsubscribers,'taglist':thisstream.taglist,'coverurl':thisstream.coverurl,'commentlist':thisstream.commentlist,'coverurl':thisstream.coverurl,'imagelist':newimagelist}
      thisuserstreams.append(currentstream)

    logging.info("Starting fetch streams subscribed to by: " + str(userid))
    stream_query = Stream.query()
    allstreams = stream_query.fetch()
    rawusersubscriptionlist = list()
    for thisstream in allstreams:
      subusers = thisstream.streamsubscribers
      if subusers.count(userid) > 0:
        rawusersubscriptionlist.append(thisstream)

    for thisstream in rawusersubscriptionlist:
      thisimagelist = thisstream.imagelist
      newimagelist = list()
      for image in thisimagelist:
        currentimage = {'imageid':image.imageid,'imagefilename':image.imagefilename,'comments':image.comments,'imagecreationdate':image.imagecreationdate,'imagefileurl':image.imagefileurl}
        newimagelist.append(currentimage)
      currentstream = {'streamname':thisstream.streamname,'creationdate':thisstream.creationdate,'viewdatelist':thisstream.viewdatelist,'viewdatelistlength':thisstream.viewdatelistlength,'owner':thisstream.owner,'subscribers':thisstream.streamsubscribers,'taglist':thisstream.taglist,'coverurl':thisstream.coverurl,'commentlist':thisstream.commentlist,'coverurl':thisstream.coverurl,'imagelist':newimagelist}
      thisusersubscriptionlist.append(currentstream)

    logging.info("This users streams: " + str(thisuserstreams))
    logging.info('subscriptionlist: ' + str(thisusersubscriptionlist))
    
    payload = {'streamlist':thisuserstreams,'subscribedstreamlist':thisusersubscriptionlist}
    result = json.dumps(payload)
    self.response.write(result)

class ViewStream(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('Input jsonis: ' + str(data))
    streamname = data['streamname']
    pagerange = data['pagerange']
    try:
      present_query = Stream.query(Stream.streamname == streamname)
      existsstream = present_query.get()
      logging.info('Query returned: ' + str(existsstream))

      removelist = list()
      #only increase view if first view where requesting page 0
      if int(pagerange[0]) == 0:
      #get viewlist for this stream and remove stale values
        existsstreamdatelist = existsstream.viewdatelist

      #TODO: Temporarily commenting out stale date value calculations
      #for date in existsstreamdatelist:
      #  if(olderthanhour(date)):
      #    logging.info("Removing item.")
      #    removelist.append(date)
      #for date in removelist:    
      #  existsstreamdatelist.remove(date)
      #  try:
      #    existsstreamdatelist.remove(date)
      #  except:
      #    logging.info('Date not found in datastore list: ' + str(date))

        existsstreamdatelist.append(str(datetime.now()))
        existsstream.viewdatelistlength = len(existsstreamdatelist)
        existsstream.viewdatelist = existsstreamdatelist
        existsstream.put()
 
      images_ds = existsstream.imagelist
      logging.info('Images list ds: ' + str(images_ds))

      #TODO - There is a bug here, if the range sent is too long we probably want to send
      # as many as we can, and right now we send nothing
      start = int(pagerange[0])
      end = int(pagerange[1])
      logging.info('Length of images_ds is: ' + str(len(images_ds)))
      if end >= len(images_ds):
        end = len(images_ds)-1
      pagerange = [start,end]
      if((start > -1) and (end >=start) and (end > -1)):
        images_ds = images_ds[start:end+1]
        logging.info('Images_ds: ' + str(images_ds))
        urls = list()
        for image in images_ds:
          urls.append(image.imagefileurl)
        payload = {'picurls': urls, 'pagerange':pagerange}
      else:
        payload = {'picurls':list(), 'pagerange':list()}
    except:
      payload = {'picurls':'','pagerange':list()}
    logging.info("Payload output is: " + str(payload))
    result = json.dumps(payload)
    self.response.write(result)


class UploadImage(webapp2.RequestHandler):

  def read_file(self, filename):
    self.response.write('Abbreviated file content (first line and last 1K):\n')
    gcs_file = gcs.open(filename)
    self.response.write(gcs_file.readline())
    gcs_file.seek(-1024, os.SEEK_END)
    self.response.write(gcs_file.read())
    gcs_file.close()

  def stat_file(self, filename):
    self.response.write('File stat:\n')
    stat = gcs.stat(filename)
    self.response.write(repr(stat))

  def create_files_for_list_bucket(self, bucket):
    self.response.write('Creating more files for listbucket...\n')
    filenames = [bucket + n for n in ['/foo1', '/foo2', '/bar', '/bar/1','/bar/2', '/boo/']]
    for f in filenames:
      create_file(f)

  def list_bucket(self, bucket):
    self.response.write('Listbucket result:\n')
    page_size = 1
    stats = gcs.listbucket(bucket + '/foo', max_keys=page_size)
    while True:
      count = 0
      for stat in stats:
        count += 1
        self.response.write(repr(stat))
        self.response.write('\n')
      if count != page_size or count == 0:
        break
    stats = gcs.listbucket(bucket + '/foo', max_keys=page_size, marker=stat.filename)

  def list_bucket_directory_mode(self, bucket):
    self.response.write('Listbucket directory mode result:\n')
    for stat in gcs.listbucket(bucket + '/b', delimiter='/'):
      self.response.write('%r' % stat)
      self.response.write('\n')
      if stat.is_dir:
        for subdir_file in gcs.listbucket(stat.filename, delimiter='/'):
          self.response.write('  %r' % subdir_file)
          self.response.write('\n')

  def post(self):
    #Get json data for image and stream ID.
    try:
      data = json.loads(self.request.body)
      logging.info('this is what Im looking for: ' + str(data))
    except:
      logging.info('No json data with this request')
    encodedimage = data['uploadimage']
    streamname = data['streamname']
    logging.info('Check if stream exists')
    present_query = Stream.query(Stream.streamname == streamname)
    existsstream = present_query.get()
    logging.info('Query returned: ' + str(existsstream))

    contenttype = data['contenttype']
    imagefilename = data['filename']
    comments = data['comments']
    creationdate = str(datetime.now().date())
    #decode the image
    imagefile = encodedimage.decode('base64')
    #create an ID for the image - may not need this....
    imageid = str(uuid.uuid1())
    bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
    logging.info("My bucket name is: " + str(bucket_name))
    #create location string for image   
    bucket = '/' + bucket_name
    filename = bucket + '/' + streamname + '/' + imageid
    try:
      if not existsstream == None:
        create_file(filename,imagefile,contenttype)
        myimage = Image(parent=ndb.Key('connexusssar', 'connexusssar'))
        logging.info('Created imagefile')
        imagefileurl = "http://storage.googleapis.com" + str(filename)
        myimage.imageid = imageid
        myimage.imagefilename = imagefilename
        myimage.comments = comments
        myimage.imagefileurl = imagefileurl
        myimage.imagecreationdate = creationdate
        myimage.imagestreamname = streamname
        myimage.put()
        thisimagelist = existsstream.imagelist
        thisimagelist.append(myimage)
        existsstream.imagelist = thisimagelist
        existsstream.put()
        logging.info("Existing streams with image list: " + str(existsstream))
        logging.info("Thisimagelist: " + str(thisimagelist))
        payload = json.dumps({"errorcode":0})
      else:
        payload = json.dumps({'errorcode':7})
        logging.info('Stream doesnt exist')


      #self.read_file(filename)
      #self.response.write('\n\n')
      #self.stat_file(filename)
      #self.response.write('\n\n')
      #self.create_files_for_list_bucket(bucket)
      #self.response.write('\n\n')
      #self.list_bucket(bucket)
      #self.response.write('\n\n')
      #self.list_bucket_directory_mode(bucket)
      #self.response.write('\n\n')

    except Exception, e:  # pylint: disable=broad-except
      logging.exception(e)
      delete_files()
      payload = json.dumps({"errorcode":1})
      self.response.write(payload)

    else:
      #delete_files()
      payload = json.dumps({"errorcode":0})
    self.response.write(payload)

class Error(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('index.html')
    templateVars = { "app_id" : AP_ID_GLOBAL, "other_html" : "" }
    fullhtml = template.render(templateVars) + "<br><br><br> Error: page coming soon</body></html>"
    self.request.write(fullhtml)

class ViewAllStreams(webapp2.RequestHandler):
  def post(self):
    logging.info('View all streams has no json input.')
    totalstreams = list()
    coverurls = list()

    logging.info('Check if stream exists')
    allstream_query = Stream.query().order(Stream.creationdate)
    allstreamsbycreation = allstream_query.fetch()
    logging.info('Query returned: ' + str(allstreamsbycreation))

    for stream in allstreamsbycreation:
      logging.info("This stream is: " + str(stream))
      totalstreams.append(stream.streamname)
      if not (stream.coverurl == ""):
        logging.info('There is a coverurl')
        coverurls.append(stream.coverurl)
      else:
        try:
          myimages = stream.imagelist
          logging.info("My images: " + str(myimages))
          thisimage = myimages[0]
          logging.info("This image: " + str(thisimage))

          coverurls.append(thisimage.imagefileurl)
          logging.info(str(thisimage.imagefileurl))
        except:
          coverurls.append("No image available")
    logging.info("Total streams: " + str(totalstreams))
    logging.info("Coverurls: " + str(coverurls))
    payload = {'streamlist':totalstreams,'coverurls':coverurls}
    result = json.dumps(payload)
    self.response.write(result)

class SearchStreams(webapp2.RequestHandler):
  def alreadyExists(self, resultList, newItem):
    for item in resultList:
      #logging.info('Looking at streamname: ' + str(item['streamname']))
      if newItem.streamname == item['streamname']:
        #logging.info('Found')
        return True
    return False

  def convertStreamObjToList(self, streamObj):
    streamObjList = streamObj.imagelist
    #logging.info('Image list from Stream object : ' + str(streamObjList))
    imageList = list()
    for img in streamObjList:
      #logging.info('img is : ' + str(img))
      imgObjList = {'comments':img.comments, 'imagecreationdate':img.imagecreationdate, 'imagefilename':img.imagefilename, 'imagefileurl':img.imagefileurl, 'imageid':img.imageid}
      imageList.append(imgObjList)
    #logging.info('imageList : ' + str(imageList))
    streamList = {'streamname':streamObj.streamname, 'creationdate':streamObj.creationdate, 'viewdatelist':streamObj.viewdatelist, 'viewdatelistlength':streamObj.viewdatelistlength, 'owner':streamObj.owner, 'subscribers':streamObj.streamsubscribers, 'taglist':streamObj.taglist, 'coverurl':streamObj.coverurl, 'commentlist':streamObj.commentlist, 'imagelist':imageList}
    return streamList

  def post(self):
    try:
      logging.info('Entering SearchStreams Handler')
      data = json.loads(self.request.body)
      logging.info('this is what Im looking for: ' + str(data))
       
      streamFilterList = data['streamname']
      logging.info('Stream filter: ' + str(streamFilterList)) 

      #get all streams
      listOfStreams = list()

      logging.info("Query to get all the streams")
      allstreams_query = Stream.query().order(Stream.creationdate)
      listOfStreams = allstreams_query.fetch()
      logging.info('Query for all streams returned:' + str(listOfStreams))

      searchResultList = list()
      for streamItem in listOfStreams:
        if streamFilterList in streamItem.streamname:
          searchResultList.append(self.convertStreamObjToList(streamItem))
          #logging.info('Stream found with name match: ' + str(streamItem))

      for streamItem in listOfStreams:
        tagList = streamItem.taglist
        for tag in tagList:
          if streamFilterList in tag:
            #if stream is not already in searchResultList then add it
            if self.alreadyExists(searchResultList, streamItem):
              logging.info('Stream ' + str(streamItem) + 'has been already found.')
            else:
              searchResultList.append(self.convertStreamObjToList(streamItem))
              #logging.info('Stream found with tag match: ' + str(streamItem))

      logging.info("SearchResultList: " + str(searchResultList))

      payload = searchResultList
    except:
      payload = {'errorcode':6}

    result = json.dumps(payload)
    self.response.write(result)

class ViewAllPageHandler(webapp2.RequestHandler):
  def post(self):
    try:
      streamname = cgi.escape(self.request.get('Streamname'))
      logging.info("Request "  + str(self.request))
      url = 'http://' + AP_ID_GLOBAL + '/ViewPage'
      mydata = json.dumps({'streamname':str(streamname),'pagerange':[0,2]})
      result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
      self.response.write(str(result.content))
    except:
      logging.info('View all page handler called post wo data')
      logging.info('Request: ' + str(self.request))


class HandleMgmtForm(webapp2.RequestHandler):

  def post(self):
    user = users.get_current_user()
    logging.info("Current user is: " + str(user))
    logging.info("Request content: " + str(self.request))
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    else:
      user = str(user.email())
    delchecked = cgi.escape(self.request.get('delete_checked'))
    unsubchecked = cgi.escape(self.request.get('unsubscribe_checked'))
    view = cgi.escape(self.request.get('view'))
    streamnames = list()
    checkboxid = ""
    try:
      #get name of stream to delete
      if not str(view) == "":
        url = 'http://' + AP_ID_GLOBAL + '/ViewPage'
        mydata = json.dumps({'streamname':str(view),'pagerange':[0,2]})
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
        self.response.write(str(result.content))
      elif delchecked == 'Delete':
        logging.info('Delete was checked')
        checkboxid = 'own'
      elif unsubchecked == 'Unsubscribe':
        logging.info('Unsub was checked')
        checkboxid = 'sub'
      logging.info("This checkbox id is: " + str(checkboxid))
      try:
        streamnames = self.request.get_all(checkboxid)
      except:
        streamnames = self.request.get(checkboxid)
      if not str(view) == "":
        logging.info('This was a view stream call')
      elif delchecked == 'Delete':
        url = 'http://' + AP_ID_GLOBAL + '/DeleteStreams'
        mydata = json.dumps({'streamnamestodelete':streamnames})
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
        self.redirect('/MgmtPage')
      elif unsubchecked == 'Unsubscribe':
        url = 'http://' + AP_ID_GLOBAL + '/UnsubscribeStreams'
        logging.info('Set url for unsubscribe')
        for substream in streamnames:
          mydata = json.dumps({'unsubuser':str(user),'streamname':str(substream)})
          result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
          logging.info(str(result.content))
          if not (str(result.content) == "{'errorcode':0}"):
            self.redirect('/Error')
        self.redirect('/MgmtPage')
    except:
      self.redirect('/Error')

class DeleteStreams(webapp2.RequestHandler):
  def post(self):
    try:
      data = json.loads(self.request.body)
      logging.info('Json data for this call: ' + str(data))
      #will take a list of streams
      deletestreams = data['streamnamestodelete']
      #iterate through list of streams input
      stream_keys = list()
      image_keys = list()
      logging.info('Before for loop')
      #TODO - there is a bug where image structured objecs are not deleted from the datestore...todo if we havemydata time
      for deletestream in deletestreams:
        logging.info("Starting fetch key for: " + str(deletestream))
        stream_query = Stream.query(Stream.streamname == deletestream)
        logging.info('Created query')
        mydeletestream = stream_query.get()
        logging.info('Query returned: ' + str(mydeletestream))
        logging.info("past query")
        logging.info("My key is: " + str(mydeletestream.key))
        stream_keys.append(mydeletestream.key)
        logging.info("Deleting stream: " + str(mydeletestream))
        rawimagestodelete = mydeletestream.imagelist
        logging.info("Raw images to delete: " + str(rawimagestodelete))
        imagestodelete = list()
        for thisimage in rawimagestodelete:
          thisurl = thisimage.imagefileurl
          image_query = Image.query(Image.imagefileurl == thisurl)
          logging.info('Created image delete query')
          mydeleteimage = image_query.get()
          logging.info('Image to delete returned from query: ' + str(mydeleteimage))
          image_keys.append(mydeleteimage.key)
          bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
          logging.info("My bucket name is: " + str(bucket_name))
          deletefilename = '/' + bucket_name + '/' + mydeleteimage.imagestreamname + '/' + mydeleteimage.imageid
          #logging.info("Imageurl object: " + str(thisurl))
          #parturl = thisurl.split('/')
          #logging.info('Parturl: ' + str(parturl))
          #parturl = parturl[3]
          #logging.info("Final parturl: " + str(parturl))
          #imagestodelete.append(parturl)
          imagestodelete.append(deletefilename)
        logging.info('Deleting: ' + str(imagestodelete))
        delete_images(imagestodelete)
      logging.info('Trying to really delete from db: ' + str(stream_keys))
      ndb.delete_multi(stream_keys)
      ndb.delete_multi(image_keys)
      logging.info('deleted from db')
      payload = {'errorcode':0}
      result = json.dumps(payload)
    except:
      payload = {'errorcode':100}
      result = json.dumps(payload)
    self.response.write(result)

class UnsubscribeStreams(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('Json data for this call: ' + str(data))
    user = data['unsubuser']
    streamname = data['streamname']
    logging.info('Check if stream exists')
    present_query = Stream.query(Stream.streamname == streamname)
    existsstream = present_query.get()
    logging.info('Query returned: ' + str(existsstream))
    userlist = existsstream.streamsubscribers
    payload = {}
    try:
      userlist.remove(user)
      logging.info("updated subscriberlist is: " + str(userlist))
      existsstream.streamsubscribers = userlist
      existsstream.put()
      payload = {'errorcode':0}
    except:
      payload = {'errorcode':8}
      logging.info('Unsubscribe user does not exist.')
    result = json.dumps(payload)
    self.response.write(result)

class SubscribeStream(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('Json data for this call: ' + str(data))
    user = data['subuser']
    streamname = data['streamname']
    logging.info('Check if stream exists')
    present_query = Stream.query(Stream.streamname == streamname)
    existsstream = present_query.get()
    logging.info('Query returned: ' + str(existsstream))
    userlist = existsstream.streamsubscribers
    payload = {}
    #TODO: Need to handle case where stream doesn't exist
    try:
      userlist.append(user)
      logging.info("updated subscriberlist is: " + str(userlist))
      existsstream.streamsubscribers = userlist
      existsstream.put()
      payload = {'errorcode':0}
    except:
      payload = {'errorcode':9}
      logging.info('Subscribe user does not exist.')
    result = json.dumps(payload)
    self.response.write(result)

class GetMostViewedStreams(webapp2.RequestHandler):
  def post(self):
    logging.info("Entering GetMostViewedStreams handler")
    data = json.loads(self.request.body)
    logging.info('No json data for this call')
    logging.info('Get all streams by most viewed')
    allstream_query = Stream.query().order(-Stream.viewdatelistlength)
    allstreamsbyviews = allstream_query.fetch()
    newmostviewedlist = list()
    for stream in allstreamsbyviews:
      thisimagelist = stream.imagelist
      logging.info('This imagelist from db: ' + str(thisimagelist))
      newimagelist = list()
      for image in thisimagelist:
        currentimage = {'imageid':image.imageid,'imagefilename':image.imagefilename,'comments':image.comments,'imagecreationdate':image.imagecreationdate,'imagefileurl':image.imagefileurl}
        logging.info('Build image object from db: ' + str(currentimage))
        newimagelist.append(currentimage)
      currentstream = {'streamname':stream.streamname,'creationdate':stream.creationdate,'viewdatelist':stream.viewdatelist,'viewdatelistlength':stream.viewdatelistlength,'owner':stream.owner,'subscribers':stream.streamsubscribers,'taglist':stream.taglist,'coverurl':stream.coverurl,'commentlist':stream.commentlist,'coverurl':stream.coverurl,'imagelist':newimagelist}
      logging.info('New current stream from db: ' + str(currentstream)) 
      newmostviewedlist.append(currentstream)
    logging.info('Returning most viewed list: ' + str(newmostviewedlist))
    payload = {'mostviewedstreams':newmostviewedlist}
    result = json.dumps(payload)
    self.response.write(result)
    logging.info("Exiting GetMostViewedStreams handler")

class Report(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('this is what Im looking for: ' + str(data))
    payload = {'errorcode':1}
    result = json.dumps(payload)
    self.response.write(result)

class DeleteAllImages(webapp2.RequestHandler):
  def post(self):
    #data = json.loads(self.request.body)
    logging.info('No json data for this call')
    delete_files()
    payload = {'errorcode':0}
    result = json.dumps(payload)
    self.response.write(result)

from google.appengine.api import mail
class email(webapp2.RequestHandler):
  def get(self):
    self.response.write(EMAIL_HTML)

class EmailHandler(webapp2.RequestHandler):
  def post(self):
    emailAddress=self.request.get('toEmail')
    subject = self.request.get('subject')
    content = self.request.get('message')
    message = mail.EmailMessage(sender="aimers1975@gmail.com", subject=subject)

    if not mail.is_email_valid(emailAddress):
      self.response.out.write("Email address is not valid.")

    message.to = emailAddress
    message.body = """%s""" %(content)
    message.send()
    self.response.out.write("Email sent successfully!")    

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class TrendingStreams(webapp.RequestHandler):
  def get(self):
    logging.info("Entering TredningStreams handler")
    self.response.write(TRENDING_STREAMS_HTML)
    logging.info("Exiting TredningStreams handler")

class TrendingStreamsHandler(webapp.RequestHandler):
  def post(self):
    global cron_rate
    checkboxValue = self.request.get('cronRate')

    logging.info('Cron rate selected: ' + str(checkboxValue))

    if checkboxValue == 'Five':
      cron_rate = 5
    elif checkboxValue == 'Hour': 
      cron_rate = 60
    elif checkboxValue == 'Day':
      cron_rate = 1440
    elif checkboxValue == 'No':
      cron_rate = -1
    logging.info("Cron Rate is now %d." % cron_rate)
    self.redirect('/TrendingPage')

class CronJobHandler(webapp.RequestHandler):
  def getTrendingStreams(self):
    #Retrieve top 3 trending streams
    url = 'http://' + AP_ID_GLOBAL + '/GetMostViewedStreams'
    params = json.dumps({})
    #logging.info('URL for GetMostViewedStreams is : ' + str(url))
    result = urlfetch.fetch(url=url, payload=params, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
    #logging.info('GetMostViewedStreams Result is: ' + str(result.content))
    resultobj = json.loads(result.content)
    trendingStreams = resultobj['mostviewedstreams']
    #logging.info('TrendingStreams from service: ' + str(trendingStreams))

    #get list of top three streams
    trendingStreamsResult = {'streamnames':list(),'imagenums':list()}
    for tstream in trendingStreams:
      #logging.info('tstream : ' + str(tstream))
      name = tstream['streamname']
      #logging.info("Trending stream : " + str(name))
      imagelist = tstream['imagelist']
      #logging.info("Trending stream image list : " + str(imagelist))
      numpics = len(imagelist)
      #logging.info('This stream imagelist: ' + str(numpics))
      if len(imagelist) == 0:
        lastnewpicdate = 'N/A'
      else:
        lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
      #logging.info("Treading stream creation date : " + lastnewpicdate)

      trendingStreamsResult['streamnames'].append(name)
      #trendingStreamsResult['dates'].append(lastnewpicdate)
      trendingStreamsResult['imagenums'].append(numpics)
    #logging.info('Top Three Trending Streams :' + str(trendingStreamsResult))
    return trendingStreamsResult

  def sendTrendEmail(self, content):
    #self.response.write('<html><body>Cron job successful.. </body></html>')
    emailAddress = "ragha@utexas.edu"
    #emailAddress = "sadaf.syed@utexas.edu"

    message = mail.EmailMessage(sender="sh.sadaf@gmail.com", subject="Connexus Trends Digest - APT")

    if not mail.is_email_valid(emailAddress):
      logging.info("The email is not valid.")
      #self.response.out.write("Email address is not valid.")

    message.to = emailAddress
    message.body = """%s""" %(content)
    message.send()
    logging.info("Message sent")
    #self.response.out.write("Message sent successfully!")
  
  def get(self):
    global last_run_time
    
    current_run_time = datetime.now()
    logging.info("Current Time: ")
    logging.info(current_run_time) 
    logging.info("Last run time: ")
    logging.info(last_run_time)
      
    elapsedTime = current_run_time - last_run_time
    elapsed = divmod(elapsedTime.total_seconds(), 60)
    elapsedMins = int(elapsed[0])

    if elapsedMins == cron_rate:
      # get top three trending streams
      #content = "Email send after " + str(elapsedMins) + " minutes."
      trendingStreams = self.getTrendingStreams();
      content = "Top 3 Trending streams are : " + str(trendingStreams['streamnames'][0]) + ", " + str(trendingStreams['streamnames'][1]) + ", "+ str(trendingStreams['streamnames'][2])
      self.sendTrendEmail(content)
      last_run_time = datetime.now()
      logging.info("Email send after %d mins" % elapsedMins)
    elif cron_rate == -1:
      last_run_time = datetime.now()
      logging.info("Trending Emails are turned off.")
    else:
      logging.info("Elapsed mins: %d" % elapsedMins)

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/UploadHandler', UploadHandler),
    ('/GetStreamData', GetStreamData),
    ('/CreateStream', CreateStream),
    ('/ManageStream', ManageStream),
    ('/ViewStream', ViewStream),
    ('/ChooseImage', ChooseImage),
    ('/serve/([^/]+)?', ServeHandler),
    ('/UploadImage', UploadImage),
    ('/Login', Login),
    ('/HandleMgmtForm', HandleMgmtForm),
    ('/MgmtPage', MgmtPage),
    ('/CreatePage', CreatePage),
    ('/ViewPage', ViewPage),
    ('/ViewPageHandler', ViewPageHandler),
    ('/SearchPage', SearchPage),
    ('/TrendingPage', TrendingPage),
    ('/SocialPage', SocialPage),
    ('/Map', Map),
    ('/ViewAllStreamsPage', ViewAllStreamsPage),
    ('/ViewAllPageHandler', ViewAllPageHandler),
    ('/SubscribeStream', SubscribeStream),
    ('/GetAllImages', GetAllImages),
    ('/ViewAllStreams', ViewAllStreams),
    ('/SearchStreams', SearchStreams),
    ('/GetMostViewedStreams', GetMostViewedStreams),
    ('/gcswrite', GCSHandler),
    ('/gcs/serve', GCSServingHandler),
    ('/DeleteStreams', DeleteStreams),
    ('/UnsubscribeStreams', UnsubscribeStreams),
    ('/Report', Report),
    ('/DeleteAllImages', DeleteAllImages),
    ('/email', email),
    ('/error', Error),
    ('/emailHandler', EmailHandler),
    ('/trends', TrendingStreams),
    ('/cronSettings', TrendingStreamsHandler),
    ('/cron/cronjob', CronJobHandler),
    ('/ErrorPage', ErrorPage)
], debug=True)
