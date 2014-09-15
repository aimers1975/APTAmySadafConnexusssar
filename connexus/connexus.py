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
#this is the list of subscriptions for quick search, key is userid, value is the list of streams they are subscribed to
subscriptions = {}
#this is the list of cover images, key us streamname, value is coverimage url.
coverimagesbystream = {}
#this is the dict of streamnames mapped to owners, to quickly search for user that owns
streamstoowner = {}
cronrate = 'five'
myimages = list()
AP_ID_GLOBAL = 'connexusssar.appspot.com'
MAIN_PAGE_HTML = """ <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<body id="main_body" >
	<div id="form_container">
		<form action="/GetStreamData" method="post">
					<div class="form_description">
			<h2>Create A Stream</h2>
			<p>Provide information about your new stream.</p>
		</div>						
			<ul >
			
					<li id="li_2" >
		<label class="description" for="element_2">Stream Name </label>
		<div>
			<input name="streamname" class="element text medium" type="text" maxlength="255" value=""/> 
		</div> 
		</li>		     <li id="li_4" >
    <label class="description" for="element_4">URL To Cover Image </label>
    <div>
      <input name="coverurl" class="element text medium" type="text" maxlength="255" value=""/> 
    </div> <p class="guidelines" id="guide_4"><small>Optional, may be left blank.</small></p>
    </li>   <li id="li_1" >
		<label class="description" for="element_1">List of subscribers </label>
		<div>
			<textarea name="subscribers" class="element textarea medium"></textarea> 
		</div><p class="guidelines" id="guide_1"><small>Comma separated list.</small></p> 
		</li>		<li id="li_3" >
		<label class="description" for="element_3">Tags </label>
		<div>
			<textarea name="tags" class="element textarea medium"></textarea> 
		</div><p class="guidelines" id="guide_3"><small>Comma separated list.</small></p> 
		</li>
			
<div><input type="submit" value="CreateStream"></div>    			</ul>
		</form>	
	</div>
	</body>
</html>"""

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
    <form action="/cron" method="post">
      <input type="checkbox" name="cronRate" value="Five"> Every 5 minutes<br>
      <input type="checkbox" name="cronRate" value="Ten"> Every 10 minutes
      <input type="submit" value="Update Rate">
    </form>
  </body>
</html>
"""

def olderthanhour(checktimestring):
  hourago = datetime.now() - timedelta(hours=1)
  if(checktimestring < hourago.isoformat()):
    return true
  else:
    return false


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

class GetStreamData(webapp2.RequestHandler):
	#Gets create stream data from the HTML page
	#Creats the json object with the streamname, subscriber emails, and tags
	#and call Create stream web service and send the json data
   def post(self):
        user  = str(users.get_current_user())
        logging.info('Current user: ' + str(user))
        streamname = cgi.escape(self.request.get('streamname'))
        subscriberdata = cgi.escape(self.request.get('subscribers'))
        subscriberlist = processSubscriberList(subscriberdata)
        tagdata = cgi.escape(self.request.get('tags'))
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

      if(not streamstoowner.has_key(streamname)):
        streamsubscribers = data['subscribers']
        addUserlistToSubscriptions(streamsubscribers,streamname)
        logging.info('\nstreamsubcribers: ' + str(streamsubscribers))

        taglist = data ['tags']
        logging.info('\nTaglist: ' + str(taglist))

        creationdate = str(datetime.now())
        logging.info('\nCreation date: ' + str(creationdate))

        owner = data['currentuser']
        logging.info('\nOwner: ' + str(owner))
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
        else:
          appstreams[owner][streamname] = thisstream
          allstreamsforsort.append(thisstream)
        logging.info('My current stream list is: ' + str(len(appstreams)))
        logging.info('Allstreamsforsort is now: ' + str(allstreamsforsort)) 
        payload = {'errorcode':0}
      else:
        logging.info('That streamname already exists')
        payload = {'errorcode':1}
    except:
      payload = {'errorcode':1}
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
      logging.info('The index found is: ' + str(index))
      logging.info('Stream: ' + str(streamname) + ' found at index: ' + str(index))
      thisstream = allstreamsforsort[index]
      logging.info("Streamdata found: " + str(thisstream))
      for x in range(0,len(allstreamsforsort[index]['viewdatelist'])):
        if(olderthanhour(allstreamsforsort[index]['viewdatelist'][x])):
          allstreamsforsort[index]['viewdatelist'].remove(allstreamsforsort[index]['viewdatelist'][x])
      allstreamsforsort[index]['viewdatelist'].append(str(datetime.now()))
      logging.info("Added view date")
      for thisindex in xrange(index,0,-1):
        logging.info('Started for loop. Thisindex is: ' + str(thisindex))
        newcount = len(allstreamsforsort[thisindex]['viewdatelist'])
        logging.info('Newcount: ' + str(newcount))
        logging.info('Allstreamsforsort: ' + str(allstreamsforsort))
        nextcount = len(allstreamsforsort[thisindex-1]['viewdatelist'])
        logging.info('Loop index is now: ' + str(thisindex))
        logging.info('Newcount: ' + str(newcount) + ' next count: ' + str(nextcount))
        if newcount > nextcount: #swap 
          temp = allstreamsforsort[thisindex-1]
          allstreamsforsort[thisindex-1] = allstreamsforsort[thisindex]
          allstreamsforsort[thisindex] = temp
        else: #we're no longer moving up the list
          break
      images = thisstream['imagelist']
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
    logging.info('Payload output is: ' + str(payload))
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
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write('Testing uploade image, about to write ' + imagefilename + ' imagefile to datastore\n ')
    self.response.write('Using bucket name: ' + bucket_name + 'Writing file for streamid: ' + streamname + '\n\n')
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
      self.response.write('\n\nThere was an error writing the file! '
                          'Please check the logs for more details.\n')

    else:
      #delete_files()
      self.response.write('\n\nThe file was successfully uploaded!\n')

#self.response.write(result)
class ViewAllStreams(webapp2.RequestHandler):
  def post(self):
    logging.info('View all streams has no json input.')
    totalstreams = list()
    coverurls = list()
    for streamlist in appstreams.itervalues():
      logging.info('streamlist from appstreams: ' + str(streamlist) + ' The type is: ' + str(type(streamlist)))
      totalstreams.append(streamlist)
      for stream in streamlist.itervalues():
        logging.info("This stream is: " + str(stream))
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
		payload = {'errorcode':1}
		result = json.dumps(payload)
		self.response.write(result)

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
          streamstoowner.pop(stream)
          logging.info("Appstreams is now: " + str(appstreams))
          logging.info('subscriptions is now: ' + str(subscriptions))
          logging.info('Allstreamsforsort is now: ' + str(allstreamsforsort))
          logging.info('streamstoowner is now: ' + str(streamstoowner))
        else:
          payload = {'errorcode':2}
          logging.info('Key not found: ' + str(stream))
      payload = {'errorcode':0}
    except:
      payload = {'errorcode':1}
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
  def get(self):
    self.response.write('<html><body>Cron job successful.. </body></html>')
    logging.info("In cronjob handler.")
    emailAddress = "aimers1975@gmail.com"

    message = mail.EmailMessage(sender=emailAddress, subject="Test Email")

    if not mail.is_email_valid(emailAddress):
      logging.info("The email is not valid.")
      self.response.out.write("Email address is not valid.")

    message.to = emailAddress
    message.send()
    logging.info("Message sent")
    self.response.out.write("Message sent successfully!")

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
    ('/cron/fivemins', CronJobHandler),
    ('/cron/tenmins', CronJobHandler)
], debug=True)
