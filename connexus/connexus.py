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
import cloudstorage as gcs
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

#Probably not necessary to change default retry params, but here for example
my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
tmp_filenames_to_clean_up = []
gcs.set_default_retry_params(my_default_retry_params)
#this is the list of streams, keys are the userid that owns the stream, each value is a list of stream
ds_key = ndb.Key('connexusssar', 'connexusssar')

cronrate = 'five'
myimages = list()
cron_rate = -1
last_run_time = datetime.now()
first_run = False
AP_ID_GLOBAL = 'connexusssar.appspot.com'

MAIN_PAGE_HTML = """<!DOCTYPE html><html><head><title>Welcome To Connexus!</title></head>
<div id="form_container"><form action="/Login" method="post"><div class="form_description"></div>           
<body><head><h1>Welcome To Connexus!</h1></head><h3>Sharing the world!<h3><br><br>
<div><input id="login_name" name="login_name" class="element text medium" type="text" maxlength="255" value="Gmail User ID"/></div></><br>
<input id="password" name="password" class="element text medium" type="text" maxlength="255" value="Gmail Password"/></div></><br>
<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="saveForm" class="button_text" type="submit" name="submit" value="Login" /></></body></html>"""
 


CREATE_STREAM_HTML =  """<div id="form_container"><form id="form_904777" form action="/GetStreamData" method="post" action=""><div class="form_description"></div>            
    <label class="description" for="streamname">Name Your Stream </label>
    <div><input id="streamname" name="streamname" class="element text medium" type="text" maxlength="255" value=""/></div> 
    <label class="description" for="subscribers">Add Subscribers </label><div>
      <textarea id="subscribers" name="subscribers" class="element textarea medium"></textarea> </div> 
    <label class="description" for="submessage">(Optional) Message For Subscribers </label><div>
      <textarea id="submessage" name="submessage" class="element textarea medium"></textarea></div> 
    <label class="description" for="tags">Tag Your Stream </label> <div>
      <input id="tags" name="tags" class="element text medium" type="text" maxlength="255" value=""/> </div> 
    <label class="description" for="coverurl">(Optional) URL For Cover Image </label>  <div>
      <input id="coverurl" name="coverurl" class="element text medium" type="text" maxlength="255" value=""/> </div> 
    <class="buttons"> <input type="hidden" name="form_id" value="904777" /> <input id="saveForm" class="button_text" type="submit" name="submit" value="Submit" /></>
      </ul>
    </form> 
  </div>
  </body>
</html>"""


HEADER_HTML = """<!DOCTYPE html><html><head><title>Connex.us!</title></head>           
<body><head><h1>Connex.us</h1></head>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Style Test</title>
<style type="text/css">
#list 
.horizontal { display: inline; border-left: 2px solid; padding-left: 0.8em; padding-right: 0.8em; }
.first { border-left: none; padding-left: 0; }
</style>
</head>

<div>
<body>
<!--Need to add links for pages once done-->
<ul id="list">
<li class="horizontal first"><a href="http://%s/MgmtPage">Manage</a></li>  
<li class="horizontal"><a href="http://%s/CreatePage">Create</a></li>
<li class="horizontal"><a href="http://%s/ViewPage">View</a></li>
<li class="horizontal first"><a href="http://%s/SearchPage">Search</a></li>
<li class="horizontal"><a href="http://%s/TrendingPage">Trending</a></li>
<li class="horizontal"><a href="http://%s/SocialPage">Social</a></li>
</ul>"""

VIEW_STREAM_HTML = """<form action="/ViewPageHandler" method="post" enctype="multipart/form-data"></div>
<input id="Streamname" name="Streamname" type="text" input style="font-size:25px" readonly="readonly" value="%s's Stream"><br>
<div><table class="tg"><tr>
    <th class="tg-031e"><img src="http://storage.googleapis.com/connexusssar.appspot.com/teststream/4d633d1c-4192-11e4-9422-bd64a46a3d3b" alt="Image Unavailable"></th>
    <th class="tg-031e"><img src="http://storage.googleapis.com/connexusssar.appspot.com/teststream/4d633d1c-4192-11e4-9422-bd64a46a3d3b" alt="Image Unavailable"></th>
    <th class="tg-031e"><img src="http://storage.googleapis.com/connexusssar.appspot.com/teststream/4d633d1c-4192-11e4-9422-bd64a46a3d3b" alt="Image Unavailable"></th>
    <th class="tg-031e"><class="buttons"><input id="More_Pictures" class="button_text" type="submit" name="More_Pictures" value="More Pictures" /></th>
  </tr>
</table></div>
<div><br><br><table class="tg"><label class="description" for="Comments">Comments</label><br><tr><textarea id="Comments" name="Comments" class="element textarea 

medium"></textarea></tr><tr><th class="tg-031e"><input id="Filename" name="Filename" class="element file" type="file"/></th></tr>
<tr><td class="tg-031e"><class="buttons"><input id="Upload" class="button_text" type="submit" name="Upload" value="Upload" /></td></tr></table><br><br></div>
<class="buttons"><input type="hidden" name="form_id" value="903438" /><input id="Subscribe" class="button_text" type="submit" name="Subscribe" value="Subscribe" />
</></body></html>"""



S_HEADER_HTML = """<!DOCTYPE html><html><head><title>Connex.us!</title></head>
<div id="form_container"><form>            
<head><h1>Connex.us</h1></head>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Style Test</title>
<style type="text/css">
#list 
.horizontal { display: inline; border-left: 2px solid; padding-left: 0.8em; padding-right: 0.8em; }
.first { border-left: none; padding-left: 0; }
</style>
</head>
<div>
<body>
<!--Need to add links for pages once done-->
<ul id="list">
<li class="horizontal first"><a href="http://%s/MgmtPage">Manage</a></li>  
<li class="horizontal"><a href="http://%s/CreatePage">Create</a></li>
<li class="horizontal"><a href="http://%s/ViewPage">View</a></li>
<li class="horizontal first"><a href="http://%s/SearchPage">Search</a></li>
<li class="horizontal"><a href="http://%s/TrendingPage">Trending</a></li>
<li class="horizontal"><a href="http://%s/SocialPage">Social</a></li>
</ul>"""

MGMT_PAGE_HTML = """<div id="form_container"><form action="/HandleMgmtForm" method="post"><div class="form_description"></div><h3>Streams I own</h3>
<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px; border-right: solid 1px; border-left: solid 1px; border-top:none; border-bottom:none; border-width:0px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:none;border-width:0px;overflow:hidden;word-break:normal;}</style>
<table class="tg">
  <tr>
    <th class="tg-031e">Name</th>
    <th class="tg-031e">Last Picture</th>
    <th class="tg-031e">Number of Pictures</th>
    <th class="tg-031e">Delete</th>
  </tr>
<!--will need to dynamically generate each ITEM based on streamlist-->
<style>
.submitLink {
background-color: transparent;
text-decoration: underline;
border: none;
color: blue;
cursor: pointer;
}
</style>
%s
</table>


<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="delete_checked" class="button_text" type="submit" name="delete_checked" value="Delete" /></></body></html>
<h3>Streams I subscribe to</h3>

<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-right: solid 1px; border-left: solid 1px; border-top: none; border-bottom: none; border-width:1px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}
</style>
<table class="tg">
  <tr>
    <th class="tg-031e">Name</th>
    <th class="tg-031e">Last Picture</th>
    <th class="tg-031e">Number of Pictures</th>
    <th class="tg-031e">Views</th>
    <th class="tg-031e">Unsubscribe</th>
  </tr>
%s
</table>

<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="unsubscribe_checked" class="button_text" type="submit" name="unsubscribe_checked" value="Unsubscribe" /></></body></html>"""

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

TRENDING_PAGE_STYLE = """\
<style>
#section {
    width:350px;
    float:left;
    padding:10px;    
}
</style>
"""

TRENDING_STREAMS_HTML = """\
<div id="section">
  <H2>Top 3 Trending Streams</H2>
<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-right: solid 1px; border-left: solid 1px; border-top: none; border-bottom: none; border-width:1px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}
</style>
<table>
%s
</table>
</div>
"""

TRENDING_REPORT_HTML = """\
<div id="aside">
  <form action="/cronSettings" method="post">
    <br>
    <input type="checkbox" name="cronRate" value="No"> No reports<br>
    <input type="checkbox" name="cronRate" value="Five"> Every 5 minutes<br>
    <input type="checkbox" name="cronRate" value="Hour"> Every 1 hour<br>
    <input type="checkbox" name="cronRate" value="Day"> Every day<br>
    <p> Email Trending Report </p>
    <input type="submit" value="Update Rate">
  </form>
</div>
"""

SEARCH_STREAMS_HTML = """\
<div id="aside">
   <form action="/SearchStreams" method="post">
     <input name="searchString" placeholder="Stream Name:">
     <input type="submit" value="Search">
   </form>
</div>
"""

SEARCH_RESULT_HTML = """\
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
NAME_LINK = '<class="buttons"><input type="hidden" name="form_id" value="903438" /><br><input id="view" class="submitLink" type="submit" name="view" value="'
NAME_LINK2 = '" />'
BEGIN = '<tr>'
START_ITEM_HTML = '<td class="tg-031e">'
END_ITEM_HTML = '</td>'

ALL_STREAMS_HTML = """\
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
  hourago = datetime.now() - timedelta(minutes=1)
  if(checktimestring < str(hourago)):
    logging.info("checktimestring: " + str(checktimestring) + " hour ago: " + str(hourago))
    logging.info("returning true")
    return True
  else:
    logging.info("checktimestring: " + str(checktimestring) + " hour ago: " + str(hourago))
    logging.info("returning false")
    return False

def generatestreamsiownlist(updatelist):
  START_CHECKBOX = '<td class="tg-031e"><input id="own" name="own" class="element checkbox" type="checkbox" value="'
  END_CHECKBOX = '" /></td></tr>'
  htmlstringfinal = ""
  length = len(updatelist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + NAME_LINK + updatelist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML + START_ITEM_HTML+ updatelist['dates'][x] + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['imagenums'][x]) + END_ITEM_HTML
    htmlstringfinal = htmlstringfinal + START_CHECKBOX + updatelist['streamnames'][x] + END_CHECKBOX
  return htmlstringfinal

def generatestreamssubscribed(updatelist):
  START_CHECKBOX = '<td class="tg-031e"><input id="sub" name="sub" class="element checkbox" type="checkbox" value="'
  END_CHECKBOX = '" /></td></tr>'
  htmlstringfinal = ""
  length = len(updatelist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + NAME_LINK + updatelist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML + START_ITEM_HTML+ updatelist['dates'][x] + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['imagenums'][x]) + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['views'][x]) + END_ITEM_HTML
    htmlstringfinal = htmlstringfinal + START_CHECKBOX + updatelist['streamnames'][x] + END_CHECKBOX
  return htmlstringfinal  

def generatetrendingstreams(trendinglist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td class="tg-031e">'
  END_ITEM_HTML = '</td>'
  htmlstringfinal = ""
  length = 3
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + trendinglist['streamnames'][x] + END_ITEM_HTML 
  return htmlstringfinal

def generatesearchedstreams(searchlist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td class="tg-031e">'
  END_ITEM_HTML = '</td>'
  htmlstringfinal = ""
  length = len(searchlist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + searchlist['streamnames'][x] + END_ITEM_HTML 
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
    logging.info('Deleting files...\n' + str(tmp_filenames_to_clean_up))
    for filename in tmp_filenames_to_clean_up:
      logging.info('Deleting file %s\n' % filename)
      try:
        gcs.delete(filename)
      except gcs.NotFoundError:
        pass

def delete_images(imagefiles):
  logging.info('Deleting image: ' + str(imagefiles))
  for filename in imagefiles:
    logging.info('Deleting image: ' + str(filename))
    try:
      gcs.delete(filename)
      logging.info('Finished deleting file')
    except gcs.NotFoundError:
      pass

class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    logging.info("Current user is: " + str(user))
    if user:
      self.response.write(MAIN_PAGE_HTML)
    else:
      self.redirect(users.create_login_url(self.request.uri))

class ViewPageHandler(webapp2.RequestHandler):
  def post(self):
    logging.info('Test View page handler:')
    try:
      imagefile = self.request.get('Filename')
      morepics = self.request.get('More_Pictures')
      logging.info('Morepics is: ' + str(morepics))
      upload = self.request.get('Upload')
      logging.info('Upload is: ' + str(upload))
      subscribe = self.request.get('Subscribe')
      logging.info("Subscribe is: " + str(subscribe))
      filename = self.request.params["Filename"].filename 
      picdata = imagefile.encode("base64")
      logging.info("filename: " + str(filename))
      (name,extension) = os.path.splitext(filename)
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
        streamname = self.request.get('Streamname')
        streamname = streamname.split("'s Str")[0]
        logging.info("Streamname is: " + str(streamname))
        comments = self.request.get('Comments')
        mydata = json.dumps({"uploadimage": picdata, "streamname": streamname, "contenttype": contenttype, "comments": comments, "filename": filename})
        url = 'http://' + AP_ID_GLOBAL + '/UploadImage'
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
        logging.info("upload image result: " + str(result.content))
      else:
        logging.info('Unrecognized image type.')
      self.redirect('/MgmtPage')
    except:
      logging.info("Problem uploading file")
      self.redirect('/Error')

class Image(ndb.Model):
  imageid = ndb.StringProperty()
  imagefilename = ndb.StringProperty()
  comments = ndb.StringProperty()
  imagefileurl = ndb.StringProperty()
  imagecreationdate = ndb.StringProperty()

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
    user = str(users.get_current_user())
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
      logging.info("This stream name is: " + str(name))
      imagelist = ownstreams['imagelist']
      logging.info('This stream imagelist: ' + str(imagelist))
      numpics = len(imagelist)
      logging.info('This stream imagelist length' + str(numpics))
      if len(imagelist) == 0:
        lastnewpicdate = 'N/A'
      else:
        lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
      logging.info("Creation date: " + lastnewpicdate)
      myupdatelist['streamnames'].append(name)
      myupdatelist['dates'].append(lastnewpicdate)
      myupdatelist['imagenums'].append(numpics)
    logging.info('My update list to generate html rows: ' + str(myupdatelist))
    for ownstreams in streamsisubscribe:
      name = ownstreams['streamname']
      logging.info("This stream name is: " + str(name))
      imagelist = ownstreams['imagelist']
      logging.info('This stream imagelist: ' + str(imagelist))
      numpics = len(imagelist)
      logging.info('This stream imagelist length' + str(numpics))
      if len(imagelist) == 0:
        lastnewpicdate = 'N/A'
      else:
        lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
      logging.info("Creation date: " + lastnewpicdate)
      myviews = ownstreams['viewdatelistlength']
      myupdatelist2['streamnames'].append(name)
      myupdatelist2['dates'].append(lastnewpicdate)
      myupdatelist2['views'].append(myviews)
      myupdatelist2['imagenums'].append(numpics)
    logging.info('My update list to generate html rows: ' + str(myupdatelist2))
    mystreamshtml = generatestreamsiownlist(myupdatelist)
    mysubscribeshtml = generatestreamssubscribed(myupdatelist2)
    logging.info("Owned streams: " + str(streamsiown))
    logging.info("Subscribed streams" + str(streamsisubscribe))
    if user:
      updatedheader = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL))
      logging.info("Updated header: " + str(updatedheader))
      fullhtml = updatedheader + (MGMT_PAGE_HTML % (mystreamshtml,mysubscribeshtml))
      self.response.write(fullhtml)
    else:
      self.redirect(users.create_login_url(self.request.uri))

class CreatePage(webapp2.RequestHandler):
  def get(self):
    fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + CREATE_STREAM_HTML
    self.response.write(fullhtml)

class ViewPage(webapp2.RequestHandler):
  def get(self):
    fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + "<br><br><br> View page coming soon</body></html>"
    self.response.write(fullhtml)

  def post(self):
      data = json.loads(self.request.body)
      logging.info('Json data sent to this function: ' + str(data))
      streamname = data['streamname']
      url = 'http://' + AP_ID_GLOBAL + '/ViewStream'
      mydata = json.dumps({'streamname':streamname,'pagerange':[0,0]})
      result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
      logging.info("ViewStream call result: " + str(result.content))
      self.response.write((HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + (VIEW_STREAM_HTML % str(streamname)))


class SearchPage(webapp2.RequestHandler):
  def get(self):
    #Retrieve top 3 trending streams
    url = 'http://' + AP_ID_GLOBAL + '/SearchStreams'
    logging.info('request: ' + str(self.request))
    searchString = self.request.get('searchString')
    logging.info('searchString is :' + searchString)

    if searchString == "":
      logging.info('searchString is null')
      fullhtml = (S_HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + SEARCH_STREAMS_HTML + "</body></html>"
      self.response.write(fullhtml)
    else:
      logging.info('searchString is not null')
      searchParams = json.dumps({'streamname':searchString})
      logging.info('URL for SearchStreams is : ' + str(url))
      result = urlfetch.fetch(url=url, payload=searchParams, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
      logging.info('SearchStreams Result is: ' + str(result.content))
      searchedStreams = json.loads(result.content)
      #searchedStreams = resultobj['mostviewedstreams']
      logging.info('SearchStreams from service: ' + str(searchedStreams))

      searchedStreamsResult = {'streamnames':list(),'imagenums':list()}
      for tstream in searchedStreams:
        name = tstream['streamname']
        logging.info("Sreached stream : " + str(name))
        imagelist = tstream['imagelist']
        logging.info("Searched stream image list : " + str(imagelist))
        numpics = len(imagelist)
        logging.info('This stream imagelist: ' + str(numpics))
        if len(imagelist) == 0:
          lastnewpicdate = 'N/A'
        else:
          lastnewpicdate = imagelist[len(imagelist)-1]['imagecreationdate']
        logging.info("Sreached stream creation date : " + lastnewpicdate)

        searchedStreamsResult['streamnames'].append(name)
        searchedStreamsResult['imagenums'].append(numpics)
      logging.info('Search returned following Streams :' + str(searchedStreamsResult))
      searchStreamHtml = generatesearchedstreams(searchedStreamsResult)
      length = len(searchedStreamsResult['streamnames'])
      searchMsg = "<p>" + str(length) + " results for " + str(searchString) + ", click on an image to view stream </p>"
      fullhtml = (S_HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + SEARCH_STREAMS_HTML + searchMsg + (SEARCH_RESULT_HTML % (searchStreamHtml)) + "</body></html>"
      self.response.write(fullhtml)

class TrendingPage(webapp2.RequestHandler):
  def get(self):
    #Retrieve top 3 trending streams
    url = 'http://' + AP_ID_GLOBAL + '/GetMostViewedStreams'
    params = json.dumps({})
    logging.info('URL for GetMostViewedStreams is : ' + str(url))
    result = urlfetch.fetch(url=url, payload=params, method=urlfetch.POST, headers={'Content-Type': 'application/json'}, deadline=30)
    logging.info('GetMostViewedStreams Result is: ' + str(result.content))
    resultobj = json.loads(result.content)
    trendingStreams = resultobj['mostviewedstreams']
    logging.info('TrendingStreams from service: ' + str(trendingStreams))

    #get list of top three streams
    trendingStreamsResult = {'streamnames':list(),'imagenums':list()}
    for tstream in trendingStreams:
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
      logging.info("Treading stream creation date : " + lastnewpicdate)

      trendingStreamsResult['streamnames'].append(name)
      #trendingStreamsResult['dates'].append(lastnewpicdate)
      trendingStreamsResult['imagenums'].append(numpics)
    logging.info('Top Three Trending Streams :' + str(trendingStreamsResult))
    trendingStreamHtml = generatetrendingstreams(trendingStreamsResult)
    logging.info('Trending Stream table html :' + str(trendingStreamHtml))

    fullhtml = (S_HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + TRENDING_PAGE_STYLE + (TRENDING_STREAMS_HTML % (trendingStreamHtml)) + TRENDING_REPORT_HTML + "</body></html>"
    #logging.info("HTML Page: " + fullhtml)
    self.response.write(fullhtml)

class SocialPage(webapp2.RequestHandler):
  def get(self):
    fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + "<br><br><br> Social page coming soon</body></html>"
    self.response.write(fullhtml)

class ViewAllStreamsPage(webapp2.RequestHandler):
  def get(self):
    fullhtml = (HEADER_HTML % (AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL,AP_ID_GLOBAL)) + "<br><br><br> View All Streams page coming soon</body></html>"
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

#Sample code we may not use
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('Filename')  # 'file' is file upload field in the form
    logging.info('Upload file from get_uploads is: ' + str(upload_files))
    blob_info = upload_files[0]
    logging.info('Blob info is: ' + str(blob_info))


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
        user  = str(users.get_current_user())
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
      if(streamname == ''):
        logging.info('Streamname is equal to empty string, we should exit.')
        payload = {'errorcode':3}
        result = json.dumps(payload)
        self.response.write(result)
        return 
      if(owner == ''):
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

        creationdate = str(datetime.now())
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
      logging.info('This imagelist from db: ' + str(thisimagelist))
      newimagelist = list()
      for image in thisimagelist:
        currentimage = {'imageid':image.imageid,'imagefilename':image.imagefilename,'comments':image.comments,'imagecreationdate':image.imagecreationdate,'imagefileurl':image.imagefileurl}
        logging.info('Build image object from db: ' + str(currentimage))
        newimagelist.append(currentimage)
      currentstream = {'streamname':thisstream.streamname,'creationdate':thisstream.creationdate,'viewdatelist':thisstream.viewdatelist,'viewdatelistlength':thisstream.viewdatelistlength,'owner':thisstream.owner,'subscribers':thisstream.streamsubscribers,'taglist':thisstream.taglist,'coverurl':thisstream.coverurl,'commentlist':thisstream.commentlist,'coverurl':thisstream.coverurl,'imagelist':newimagelist}
      logging.info('New current stream from db: ' + str(currentstream))
      thisuserstreams.append(currentstream)

    logging.info("Starting fetch streams subscribed to by: " + str(userid))
    stream_query = Stream.query()
    allstreams = stream_query.fetch()
    rawusersubscriptionlist = list()
    for thisstream in allstreams:
      subusers = thisstream.streamsubscribers
      logging.info("Stream: " + str(thisstream) + " has subscribers: " + str(subusers))
      if subusers.count(userid) > 0:
        rawusersubscriptionlist.append(thisstream)

    for thisstream in rawusersubscriptionlist:
      thisimagelist = thisstream.imagelist
      logging.info('This imagelist from db: ' + str(thisimagelist))
      newimagelist = list()
      for image in thisimagelist:
        currentimage = {'imageid':image.imageid,'imagefilename':image.imagefilename,'comments':image.comments,'imagecreationdate':image.imagecreationdate,'imagefileurl':image.imagefileurl}
        logging.info('Build image object from db: ' + str(currentimage))
        newimagelist.append(currentimage)
      currentstream = {'streamname':thisstream.streamname,'creationdate':thisstream.creationdate,'viewdatelist':thisstream.viewdatelist,'viewdatelistlength':thisstream.viewdatelistlength,'owner':thisstream.owner,'subscribers':thisstream.streamsubscribers,'taglist':thisstream.taglist,'coverurl':thisstream.coverurl,'commentlist':thisstream.commentlist,'coverurl':thisstream.coverurl,'imagelist':newimagelist}
      logging.info('New current stream from db: ' + str(currentstream))
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
      logging.info('Check if stream exists')
      present_query = Stream.query(Stream.streamname == streamname)
      existsstream = present_query.get()
      logging.info('Query returned: ' + str(existsstream))

      removelist = list()

      #get viewlist for this stream and remove stale values
      existsstreamdatelist = existsstream.viewdatelist
      logging.info('view date list from datastore is: ' + str(existsstreamdatelist))

      for date in existsstreamdatelist:
        logging.info("Calling older than hour with input: " + str(date))
        if(olderthanhour(date)):
          logging.info("Removing item.")
          removelist.append(date)
      for date in removelist:    
        existsstreamdatelist.remove(date)
        try:
          existsstreamdatelist.remove(date)
        except:
          logging.info('Date not found in datastore list: ' + str(date))

      logging.info('Past for loops for datelist')

      existsstreamdatelist.append(str(datetime.now()))
      existsstream.viewdatelistlength = len(existsstreamdatelist)
      existsstream.viewdatelist = existsstreamdatelist
      logging.info('existsstreamdatelist: ' + str(existsstreamdatelist))
      existsstream.put()
 
      images_ds = existsstream.imagelist
      logging.info('Images list ds: ' + str(images_ds))

      #TODO - There is a bug here, if the range sent is too long we probably want to send
      # as many as we can, and right now we send nothing
      start = int(pagerange[0])
      logging.info('Pagerange start: ' + str(start))
      end = int(pagerange[1])
      logging.info('Pagerange end: ' + str(end))
      logging.info('Length of images_ds is: ' + str(len(images_ds)))
      if ((start > -1) and ((end+1) <= len(images_ds))):
        images_ds = images_ds[start:end+1]
        logging.info('Images_ds: ' + str(images_ds))
        urls = list()
        for image in images_ds:
          logging.info("This image is: " + str(image) + ' and imageurl is: ' + str(image.imagefileurl))
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
    creationdate = str(datetime.now())
    #decode the image
    imagefile = encodedimage.decode('base64')
    #create an ID for the image - may not need this....
    imageid = str(uuid.uuid1())
    bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
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
        myimage.put()
        thisimagelist = existsstream.imagelist
        thisimagelist.append(myimage)
        existsstream.imagelist = thisimagelist
        existsstream.put()
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
    self.request.write(HEADER_HTML + "<br><br><br> Create page coming soon</body></html>")

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
      coverurls.append(stream.coverurl)

    logging.info("Total streams: " + str(totalstreams))
    logging.info("Coverurls: " + str(coverurls))
    payload = {'streamlist':totalstreams,'coverurls':coverurls}
    result = json.dumps(payload)
    self.response.write(result)

class SearchStreams(webapp2.RequestHandler):
  def convertStreamObjToList(self, streamObj):
    streamList = {'streamname':streamObj.streamname, 'creationdate':streamObj.creationdate, 'viewdatelist':streamObj.viewdatelist, 'viewdatelistlength':streamObj.viewdatelistlength, 'owner':streamObj.owner, 'subscribers':streamObj.streamsubscribers, 'taglist':streamObj.taglist, 'coverurl':streamObj.coverurl, 'commentlist':streamObj.commentlist, 'imagelist':streamObj.imagelist}
    return streamList

  def post(self):
    logging.info('Entering SerachStreams Handler')
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

    streamFilter = streamFilterList[0]
    
    searchResultList = list()
    for streamItem in listOfStreams:
      if streamFilter in streamItem.streamname:
        searchResultList.append(self.convertStreamObjToList(streamItem))
        #logging.info('Stream found with name match: ' + str(streamItem))

    for streamItem in listOfStreams:
      tagList = streamItem.taglist
      for tag in tagList:
        if streamFilter in tag:
          searchResultList.append(self.convertStreamObjToList(streamItem))
          #logging.info('Stream found with tag match: ' + str(streamItem))

    logging.info("SearchResultList: " + str(searchResultList))

    result = json.dumps(searchResultList)
    #payload = {'errorcode':1}
    #result = json.dumps(payload)
    #self.response.write('<html><body>')
    #self.response.write('Allstreamsforsort: ' + str(result))
    #self.response.write('</body></html>')
    self.response.write(result)
    logging.info('Exiting SerachStreams Handler')

class HandleMgmtForm(webapp2.RequestHandler):


  def post(self):
    user = users.get_current_user()
    logging.info("Current user is: " + str(user))
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    logging.info("Management form data: " + str(self.request))
    delchecked = cgi.escape(self.request.get('delete_checked'))
    unsubchecked = cgi.escape(self.request.get('unsubscribe_checked'))
    view = cgi.escape(self.request.get('view'))
    logging.info('View Retrieved: ' + str(view))
    streamnames = list()
    checkboxid = ""
    try:
      #get name of stream to delete
      if not str(view) == "":
        logging.info('We need to switch to view page')
        url = 'http://' + AP_ID_GLOBAL + '/ViewPage'
        mydata = json.dumps({'streamname':str(view)})
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'},deadline=30)
        self.response.write(str(result.content))
        viewhtml = str(result.content)
        logging.info(viewhtml)
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
      logging.info("From checkbox we got streams: " + str(streamnames))
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
          logging.info('Looping through streams: ' + str(substream))
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
      logging.info('Before for loop')
      #TODO - there is a bug where image structured objecs are not deleted from the datestore...todo if we havemydata time
      for deletestream in deletestreams:
        logging.info("Starting fetch key for: " + str(deletestream))
        stream_query = Stream.query(Stream.streamname == deletestream)
        logging.info('Created query')
        mydeletestream = stream_query.get()
        logging.info("past query")
        logging.info("My key is: " + str(mydeletestream.key))
        stream_keys.append(mydeletestream.key)
        logging.info("Deleting stream: " + str(mydeletestream))
        rawimagestodelete = mydeletestream.imagelist
        logging.info("Raw images to delete: " + str(rawimagestodelete))
        imagestodelete = list()
        for thisimage in rawimagestodelete:
          thisurl = thisimage.imagefileurl
          logging.info("Imageurl object: " + str(thisurl))
          parturl = thisurl.split('http://storage.googleapis.com')[1]
          logging.info('Parturl: ' + str(parturl))
          imagestodelete.append(parturl)
        logging.info('Deleting: ' + str(imagestodelete))
        delete_images(imagestodelete)
      logging.info('Trying to really delete from db: ' + str(stream_keys))
      ndb.delete_multi(stream_keys)
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
    message = mail.EmailMessage(sender="sh.sadaf@gmail.com", subject=subject)

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
    logging.info('URL for GetMostViewedStreams is : ' + str(url))
    result = urlfetch.fetch(url=url, payload=params, method=urlfetch.POST, headers={'Content-Type': 'application/json'})
    logging.info('GetMostViewedStreams Result is: ' + str(result.content))
    resultobj = json.loads(result.content)
    trendingStreams = resultobj['mostviewedstreams']
    logging.info('TrendingStreams from service: ' + str(trendingStreams))

    #get list of top three streams
    trendingStreamsResult = {'streamnames':list(),'imagenums':list()}
    for tstream in trendingStreams:
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
      logging.info("Treading stream creation date : " + lastnewpicdate)

      trendingStreamsResult['streamnames'].append(name)
      #trendingStreamsResult['dates'].append(lastnewpicdate)
      trendingStreamsResult['imagenums'].append(numpics)
    logging.info('Top Three Trending Streams :' + str(trendingStreamsResult))
    return trendingStreamsResult

  def sendTrendEmail(self, content):
    #self.response.write('<html><body>Cron job successful.. </body></html>')
    emailAddress = "sadaf.syed@utexas.edu"

    message = mail.EmailMessage(sender="sh.sadaf@gmail.com", subject="Test Email")

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
      content = "Top 3 Trending streams are : " + str(trendingStreams)
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
    ('/GetStreamData', GetStreamData),
    ('/CreateStream', CreateStream),
    ('/ManageStream', ManageStream),
    ('/ViewStream', ViewStream),
    ('/ChooseImage', ChooseImage),
    ('/upload', UploadHandler),
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
    ('/ViewAllStreamsPage', ViewAllStreamsPage),
    ('/SubscribeStream', SubscribeStream),
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
    ('/cron/cronjob', CronJobHandler)
], debug=True)
