from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import app_identity
from datetime import datetime,timedelta
from time import gmtime, strftime
import cloudstorage as gcs
import webapp2
import logging
import json
import cgi
import urllib
import re
import os
import uuid

#Probably not necessary to change default retry params, but here for example
my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
tmp_filenames_to_clean_up = []
gcs.set_default_retry_params(my_default_retry_params)
#this is the list of streams, keys are the userid that owns the stream, each value is a list of stream
appstreams = {}
allstreamsforsort = list()
allstreamsbycreationtime = list()
#this is the list of subscriptions for quick search, key is userid, value is the list of streams they are subscribed to
subscriptions = {}
#this is the list of cover images, key us streamname, value is coverimage url.
coverimagesbystream = {}
#this is the dict of streamnames mapped to owners, to quickly search for user that owns
streamstoowner = {}
cronrate = 'five'
myimages = list()
cron_rate = 60
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

MGMT_PAGE_HTML = """<!DOCTYPE html><html><head><title>Connex.us!</title></head>
<div id="form_container"><form action="/HandleMgmtForm" method="post"><div class="form_description"></div>            
<body><head><h1>Connex.us</h1></head><h3>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Style Test</title>
<style type="text/css">
#list 
.horizontal { display: inline; border-left: 2px solid; padding-left: 0.8em; padding-right: 0.8em; }
.first { border-left: none; padding-left: 0; }
</style>
</head>
<body>
<!--Need to add links for pages once done-->
<ul id="list">
<li class="horizontal first">Manage</li>
<li class="horizontal">Create</li>
<li class="horizontal">View</li>
<li class="horizontal first">Search</li>
<li class="horizontal">Trending</li>
<li class="horizontal">Social</li>
</ul>

<h3>Streams I own</h3>
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
<!--will need to dynamically generate each row based on streamlist-->
  <tr>
    <td class="tg-031e">test2</td>
    <td class="tg-031e"></td>
    <td class="tg-031e"></td>
<!--When dynamically genenerating will need each checkbox tied to streamname-->
    <td class="tg-031e"><input id="element_1_1" name="element_1_1" class="element checkbox" type="checkbox" value="1" />
</td>
  </tr>
</table>

<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="delete_checked" class="button_text" type="submit" name="delete_checked" value="Delete Checked Streams" /></></body></html>
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
  <tr>
    <td class="tg-031e">test2</td>
    <td class="tg-031e"></td>
    <td class="tg-031e"></td>
    <td class="tg-031e"></td>
    <td class="tg-031e"><input id="element_1_1" name="element_1_1" class="element checkbox" type="checkbox" value="1" />
</td>
  </tr>
</table>

<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="unsubscribe_checked" class="button_text" type="submit" name="unsubscribe_checked" value="Unsubscribe Checked Streams" /></></body></html>"""

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

TRENDING_STREAMS_HTML = """\
<html>
  <body>
    <H2>Top 3 Trending Streams</H2>
    <form action="/cron/cronjob" method="post">
      <input type="checkbox" name="cronRate" value="Five"> Every 5 minutes<br>
      <input type="checkbox" name="cronRate" value="Ten"> Every 10 minutes
      <input type="submit" value="Update Rate">
    </form>
  </body>
</html>
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


def addcoverurl(coverurl,streamname):
  logging.info('In add coverurl for ' + str(streamname) + ' at ' + coverurl)
  coverurl[streamname] = coverurl
    
def addUserlistToSubscriptions(userlist,streamname):
  logging.info("In add users to subscriptions")
  for user in userlist:
    logging.info("Interating through this user: " + str(user))
    if (subscriptions.has_key(user)):
      logging.info("\nFound key\n")
      subscriptions[user].append(streamname)
    else:
      logging.info("\nKey not found, trying to create list and append\n")
      subscriptions[user] = list()
      logging.info("\nNew list created, appending...\n")
      subscriptions[user].append(streamname)
  logging.info('Subscriber list updated: ' + str(subscriptions))

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

class MgmtPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    logging.info("Current user is: " + str(user))
    if user:
      self.response.write(MGMT_PAGE_HTML)
    else:
      self.redirect(users.create_login_url(self.request.uri))

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
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
    logging.info('Upload file from get_uploads is: ' + str(upload_files))
    blob_info = upload_files[0]
    logging.info('Blob info is: ' + str(blob_info))
    redirectstring = '/serve/' + str(blob_info.key())
    logging.info('Redirecting, Redirect url is: ' + redirectstring) 
    self.redirect(redirectstring)

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
        prejson = {'streamname':streamname,'subscribers':subscriberlist,'tags':taglist,'coverurl':coverurl,'currentuser':user}
        mydata = json.dumps(prejson)
        logging.info('JSON data: ', str(mydata))
        url = 'http://' + AP_ID_GLOBAL + '/CreateStream'
        result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        logging.info("Create stream call result: " + str(result.content))


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
      if(not streamstoowner.has_key(streamname)):
        streamsubscribers = data['subscribers']
        addUserlistToSubscriptions(streamsubscribers,streamname)
        logging.info('\nstreamsubcribers: ' + str(streamsubscribers))

        taglist = data ['tags']
        logging.info('\nTaglist: ' + str(taglist))

        creationdate = str(datetime.now())
        logging.info('\nCreation date: ' + str(creationdate))

        streamstoowner[streamname] = owner

        viewdatelist = list()
        logging.info('\nViewdatelist: ' + str(viewdatelist))

        commentlist = list()
        logging.info('\nCommentlist: ' + str(commentlist))

        coverurl = data['coverurl']
        logging.info('\nCoverurl: ' + str(coverurl))

        imagelist = list()
        logging.info('\nImagelist: ' + str(imagelist))
        thisstream = {'streamname':streamname,'creationdate':creationdate,'viewdatelist':viewdatelist,'owner':owner,'subscriberlist':streamsubscribers,'taglist':taglist,'coverurl':coverurl,'commentlist':commentlist,'coverurl':coverurl,'imagelist':imagelist}
        if (not appstreams.has_key(owner)):
          appstreams[owner] = {streamname:thisstream}
          allstreamsforsort.append(thisstream)
          allstreamsbycreationtime.append(thisstream)
        else:
          appstreams[owner][streamname] = thisstream
          allstreamsforsort.append(thisstream)
          allstreamsbycreationtime.append(thisstream)
        logging.info('My current stream list is: ' + str(len(appstreams)))
        logging.info('Allstreamsforsort is now: ' + str(allstreamsforsort)) 
        payload = {'errorcode':0}
      else:
        logging.info('That streamname already exists')
        payload = {'errorcode':1}
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
    logging.info('Appstreams: ' + str(appstreams))
    if(subscriptions.has_key(userid)):
      logging.info('This user has subscriptions: ' + str(userid))
      thisusersubscriptions = subscriptions[userid]
    else:
      logging.info(str(userid) + ' not found, returning empty subscription lists')
      thisusersubscriptions = list()
    if(appstreams.has_key(userid)):
      logging.info('This user has streams: ' + str(userid))
      thisuserstreams = appstreams[userid]
    else:
      logging.info(str(userid) + ' not found, return empty streamlist')
      thisuserstreams = list()
    thisusersubscriptionlist = list()
    logging.info('allstreamsforsort is now: ' + str(allstreamsforsort))
    logging.info('subscriptions are: ' + str(thisusersubscriptions))
    for name in thisusersubscriptions:
      logging.info("Looking for stream: " + name)
      currentstream = appstreams[streamstoowner[name]][name]
      logging.info('Current stream appending to subscribed list: ' + str(currentstream))
      thisusersubscriptionlist.append(currentstream)
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
      logging.info('streamstoowner[streamname]: ' + str(streamstoowner[streamname]) )
      currentstream = appstreams[streamstoowner[streamname]][streamname]
      logging.info('The stream retrieved for viewing is: ' + str(currentstream))
      index = allstreamsforsort.index(currentstream)
      logging.info('Stream: ' + str(streamname) + ' found at index: ' + str(index))
      removelist = list()
      logging.info("Viewdatelist length: " + str(len(allstreamsforsort[index]['viewdatelist'])))
      for date in allstreamsforsort[index]['viewdatelist']:
        logging.info("Calling older than hour with input: " + str(date))
        if(olderthanhour(date)):
          logging.info("Removing item.")
          removelist.append(date)
      for date in removelist:    
        allstreamsforsort[index]['viewdatelist'].remove(date)
      allstreamsforsort[index]['viewdatelist'].append(str(datetime.now()))
      logging.info("Viewdatelist length: " + str(len(allstreamsforsort[index]['viewdatelist'])))
      allstreamsforsort.remove(currentstream)
      logging.info("removed allstream for sort index")
      if len(allstreamsforsort) > 0:
        for x in range(0,len(allstreamsforsort)):
          logging.info("Starting for loop x=" + str(x))
          if len(currentstream['viewdatelist']) < len(allstreamsforsort[x]['viewdatelist']):
            if (x == (len(allstreamsforsort)-1)):
              logging.info('End of list, insert at end')
              allstreamsforsort.insert(len(allstreamsforsort),currentstream)
              break
            else:
              logging.info('keep going')
          else:
            logging.info('found spot at: ' + str(x))
            allstreamsforsort.insert(x, currentstream)
            break
      else:
        logging.info("Allstreamsforsort length is 0")
        allstreamsforsort.append(currentstream)
      logging.info(str(allstreamsforsort))
      images = currentstream['imagelist']
      logging.info('Images list: ' + str(images))
      start = int(pagerange[0])
      logging.info('Pagerange start: ' + str(start))
      end = int(pagerange[1])
      logging.info('Pagerange end: ' + str(end))
      logging.info('Length of images is: ' + str(len(images)))
      if ((start > -1) and ((end+1) <= len(images))):
        images = images[start:end+1]
        urls = list()
        for image in images:
          urls.append(image['imageurl'])
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
    contenttype = data['contenttype']
    imagefilename = data['filename']
    comments = data['comments']
    #decode the image
    imagefile = encodedimage.decode('base64')
    #create an ID for the image - may not need this....
    imageid = str(uuid.uuid1())
    bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
    #create location string for image   
    bucket = '/' + bucket_name
    filename = bucket + '/' + streamname + '/' + imageid
    try:
      create_file(filename,imagefile,contenttype)
      logging.info('Created imagefile')
      self.response.write('\n\n')
      #Once image successfully created, add Image to the image list in stream
      imagefileurl = "http://storage.googleapis.com" + str(filename)
      thisimage = {'imageid':imageid,'filename':imagefilename,'comments':comments,'imageurl':imagefileurl}
      logging.info('Image object created: ' + str(thisimage))
      logging.info("starting stream search loop")
      logging.info("My streams: " + str(appstreams))
      for streamlist in appstreams.itervalues():
        if streamlist.has_key(streamname):
          streamlist[streamname]['imagelist'].append(thisimage)
      logging.info("Appstreams: " + str(appstreams))
      payload = json.dumps({"errorcode":0})
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


class ViewAllStreams(webapp2.RequestHandler):
  def post(self):
    logging.info('View all streams has no json input.')
    totalstreams = list()
    coverurls = list()
    for stream in allstreamsbycreationtime:
        logging.info("This stream is: " + str(stream))
        totalstreams.append(stream['streamname'])
        coverurls.append(stream['coverurl'])
    for stream in allstreamsforsort: 
      stream['viewdatelist'].append(str(datetime.now()))
    logging.info("Total streams: " + str(totalstreams))
    logging.info("Coverurls: " + str(coverurls))
    payload = {'streamlist':totalstreams,'coverurls':coverurls}
    result = json.dumps(payload)
    self.response.write(result)

class SearchStreams(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('this is what Im looking for: ' + str(data))
     
    streamFilterList = data['streamname']
    logging.info('Stream filter: ' + str(streamFilterList)) 

    streamFilter = streamFilterList[0]
    
    searchResultList = list()
    for streamItem in allstreamsforsort:
      if streamFilter in streamItem['streamname']:
        searchResultList.append(streamItem)
        #logging.info('Stream found with name match: ' + str(streamItem))

    for streamItem in allstreamsforsort:
      tagList = streamItem['taglist']
      for tag in tagList:
        if streamFilter in tag:
          searchResultList.append(streamItem)
          #logging.info('Stream found with tag match: ' + str(streamItem))

    logging.info("SearchResultList: " + str(searchResultList))

    result = json.dumps(searchResultList)
    #payload = {'errorcode':1}
    #result = json.dumps(payload)
    self.response.write(result)

class HandleMgmtForm(webapp2.RequestHandler):
  def post(self):
    #login = cgi.escape(self.request.get(''))
    logging.info("Management form data: " + str(self.request))

class DeleteStreams(webapp2.RequestHandler):
  def post(self):
    try:
      data = json.loads(self.request.body)
      logging.info('Json data for this call: ' + str(data))
      #will take a list of streams
      deletestreams = data['streamnamestodelete']
      #iterate through list of streams input
      for stream in deletestreams:
        logging.info("Deleting streamname: " + str(stream))
        if streamstoowner.has_key(stream):
          subscribed = appstreams[streamstoowner[stream]][stream]['subscriberlist']
          logging.info('Subscribers are: ' + str(subscribed))
          thisstream = appstreams[streamstoowner[stream]][stream]
          imageobjects = thisstream['imagelist']
          imagestodelete = list()
          for imageurl in imageobjects:
            logging.info("Image url object: " + str(imageurl))
            thisurl = imageurl['imageurl']
            logging.info('This url: ' + str(thisurl))
            parturl = thisurl.split('http://storage.googleapis.com')[1]
            logging.info('Parturl: ' + str(parturl))
            imagestodelete.append(parturl)
          logging.info('Deleting: ' + str(imagestodelete))
          delete_images(imagestodelete)
          logging.info('Delete stream: ' + str(thisstream))
          for user in subscribed:
            logging.info('Removing subscription for ' + str(user) + ' in stream ' + str(stream))
            subscriptions[user].remove(stream)
            if (len(subscriptions[user]) == 0):
              subscriptions.pop(user)
          appstreams[streamstoowner[stream]].pop(stream)
          if (len(appstreams[streamstoowner[stream]]) == 0):
            appstreams.pop(streamstoowner[stream])
          allstreamsforsort.remove(thisstream)
          allstreamsbycreationtime.remove(thisstream)
          streamstoowner.pop(stream)
          logging.info("Appstreams is now: " + str(appstreams))
          logging.info('subscriptions is now: ' + str(subscriptions))
          logging.info('Allstreamsforsort is now: ' + str(allstreamsforsort))
          logging.info('streamstoowner is now: ' + str(streamstoowner))
        else:
          payload = {'errorcode':4}
          logging.info('Key not found: ' + str(stream))
      payload = {'errorcode':0}
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
    appstreams[streamstoowner[streamname]][streamname]['subscriberlist'].remove(user)
    subscriptions[user].remove(streamname)
    if (len(subscriptions[user]) == 0):
      subscriptions.pop(user)
    logging.info('Appstreams is now: ' + str(appstreams))
    logging.info('Subscriptions is now' + str(subscriptions))
    logging.info('Allstreamsforsort is now ' + str(allstreamsforsort))
    payload = {'errorcode':0}
    result = json.dumps(payload)
    self.response.write(result)

class GetMostViewedStreams(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    logging.info('No json data for this call')
    payload = {'mostviewedstreams':allstreamsforsort}
    result = json.dumps(payload)
    self.response.write(result)

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
    self.response.write(TRENDING_STREAMS_HTML)

class TrendingStreamsHandler(webapp.RequestHandler):
  def post(self):
    checkboxValue = self.request.get('cronRate')
    self.response.write('<html><body>Cron Rate is: <pre>')
    self.response.write(cgi.escape(self.request.get('cronRate')))
    self.response.write('</pre></body></html>')

    logging.info('Cron rate selected: ' + str(checkboxValue))

    five = 'Five'
    if checkboxValue == 'Five':
      logging.info("Found checkbox five.")
      self.response.write('<html><body>Cron Rate is Five')
      self.response.write('</body></html>')
      cronjob = '/cron/fivemins'
      logging.info("Redirecing to cronjob fivemin.")
      self.redirect(cronjob)
    else:
      logging.info("Found checkbox 10.")
      self.response.write('<html><body>Cron Rate is Ten')
      self.response.write('</body></html>')
      cronjob = '/cron/tenmins'
      logging.info("Redirecing to cronjob fivemin.")
      self.redirect(cronjob)

class CronJobHandler(webapp.RequestHandler):
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
      content = "Email send after " + str(elapsedMins) + " minutes."
      self.sendTrendEmail(content)
      last_run_time = datetime.now()
      logging.info("Email send after %d mins" % elapsedMins)
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
    ('/emailHandler', EmailHandler),
    ('/trends', TrendingStreams),
    ('/cronSettings', TrendingStreamsHandler),
    ('/cron/cronjob', CronJobHandler)
], debug=True)
