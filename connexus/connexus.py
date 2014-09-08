from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import cloudstorage as gcs
import webapp2
import logging
import json
import cgi
import urllib
import re
import jinja2
import os

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
		</li>		<li id="li_1" >
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

def CreateFile(filename):
  """Create a GCS file with GCS client lib.
  Args:
    filename: GCS filename.
  Returns:
    The corresponding string blobkey for this GCS file.
  """
  # Create a GCS file with GCS client.
  with gcs.open(filename, 'w') as f:
    f.write('abcde\n')
  # Blobstore API requires extra /gs to distinguish against blobstore files.
  blobstore_filename = '/gs' + filename
  # This blob_key works with blobstore APIs that do not expect a
  # corresponding BlobInfo in datastore.
  return blobstore.create_gs_key(blobstore_filename)

class MainPage(webapp2.RequestHandler):

    def get(self):
    	user = users.get_current_user()
    	if user:
    		self.response.write(MAIN_PAGE_HTML)
    	else:
    		self.redirect(users.create_login_url(self.request.uri))

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


class GCSServingHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
    blob_key = CreateFile('/' + AP_ID_GLOBAL + '/blobstore_serving_demo')
    self.send_blob(blob_key)

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
    logging.info('Upload file from get_uploads is: ' + str(upload_files))
    blob_info = upload_files[0]
    logging.info('Blob info is: ' + str(blob_info))
    redirectstring = '/serve/' + str(blob_info.key())
    logging.info('Redirecting, Redirect url is: ' + redirectstring) 
    self.redirect(redirectstring)

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
   	    streamname = cgi.escape(self.request.get('streamname'))
   	    subscriberdata = cgi.escape(self.request.get('subscribers'))
   	    subscriberlist = processSubscriberList(subscriberdata)
   	    tagdata = cgi.escape(self.request.get('tags'))
   	    taglist = processTagList(tagdata)
   	    self.response.write('<html><body>Processed stream info: <pre>')
   	    self.response.write('Stream name: ' + str(streamname))
   	    self.response.write('<br>')
   	    self.response.write('Subscriber list: <br>')
   	    for subscriber in subscriberlist:
   	    	self.response.write(subscriber)
   	    	self.response.write('<br>')
   	    self.response.write('Tags: ' + str(tagdata))
   	    self.response.write('</pre></body></html>')
   	    prejson = {'streamname':streamname,'subscribers':subscriberlist,'tags':taglist}
   	    mydata = json.dumps(prejson)
   	    #This needs to be changes when uploaded
   	    #url = 'http://localhost:8080/CreateStream'
   	    url = 'http://' + AP_ID_GLOBAL + '/CreateStream'
   	    result = urlfetch.fetch(url=url, payload=mydata, method=urlfetch.POST, headers={'Content-Type': 'application/json'})
   	    logging.info("Create stream call result: " + str(result.content))


class CreateStream(webapp2.RequestHandler):
   #Eventually this will create the stream, for now it retrieves 
   #the json data from the post request and logs the json
   #data received to the console.  This is hardcoded to return a
   #json object with the error code which currently means nothing.
   def post(self):
   	   data = json.loads(self.request.body)
   	   logging.info('this is what Im looking for: ' + str(data))
   	   #get inputs
   	   #create stream object
   	   #capture stream creation time
   	   #store stream to datastore
   	   #keys?
   	   payload = {'errorcode':1}
   	   result = json.dumps(payload)
   	   self.response.write(result)

class ChooseImage(webapp2.RequestHandler):
  def get(self):
    upload_url = blobstore.create_upload_url('/upload')
    self.response.out.write('<html><body>')
    logging.info('The upload URL is: ' + str(upload_url))
    urlhtml = '<form action="' + upload_url + '" method="post" enctype="multipart/form-data">'
    logging.info('URL HTML: ' + urlhtml)
    self.response.out.write(urlhtml)
    self.response.out.write('Upload File: <input type="file" name="file"><br> <input type="submit" name="submit" value="Submit"> </form></body></html>')

class ManageStream(webapp2.RequestHandler):
	def post(self):
	   data = json.loads(self.request.body)
   	   logging.info('this is what Im looking for: ' + str(data))
   	   #get inputs
   	   #find streams by user id and retrieve them
   	   #create json object for two streams and return them
   	   payload = {'errorcode':1}
   	   result = json.dumps(payload)
   	   self.response.write(result)

class ViewStream(webapp2.RequestHandler):
	def post(self):
		data = json.loads(self.request.body)
		logging.info('this is what Im looking for: ' + str(data))
		payload = {'errorcode':1}
		result = json.dumps(payload)
		self.response.write(result)

class UploadImage(webapp2.RequestHandler):
  def get(self):
    #This is not working yet, just writes some data to GCS and returns it
    upload_url = 'http://' + AP_ID_GLOBAL + '/gcswrite'
    logging.info('Upload url for gcs: ' + str(upload_url))
    #data = json.loads(self.request.body)
    #logging.info('this is what Im looking for: ' + str(data))
    #result = urlfetch.fetch(url=upload_url, method=urlfetch.GET)
    self.redirect('/gcswrite')
    #logging.info("URLFetch result: " + str(result.content))
    #payload = {'errorcode':1}
    #result = json.dumps(payload)

#self.response.write(result)
class ViewAllStreams(webapp2.RequestHandler):
	def post(self):
		data = json.loads(self.request.body)
		logging.info('this is what Im looking for: ' + str(data))
		payload = {'errorcode':1}
		result = json.dumps(payload)
		self.response.write(result)

class SearchStreams(webapp2.RequestHandler):
	def post(self):
		data = json.loads(self.request.body)
		logging.info('this is what Im looking for: ' + str(data))
		payload = {'errorcode':1}
		result = json.dumps(payload)
		self.response.write(result)

class GetMostViewedStreams(webapp2.RequestHandler):
	def post(self):
		data = json.loads(self.request.body)
		logging.info('this is what Im looking for: ' + str(data))
		payload = {'errorcode':1}
		result = json.dumps(payload)
		self.response.write(result)

class Report(webapp2.RequestHandler):
	def post(self):
		data = json.loads(self.request.body)
		logging.info('this is what Im looking for: ' + str(data))
		payload = {'errorcode':1}
		result = json.dumps(payload)
		self.response.write(result)

from google.appengine.api import mail
jinja_environment = jinja2.Environment(autoescape=True,loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class email(webapp2.RequestHandler):
  template = jinja_environment.get_template('email.html')
  def get(self):
    self.response.out.write(self.template.render())
  def post(self):
  # get email info
    emailAddress=self.request.get("toEmail")
    emailSubject=self.request.get("subject")
    emailMessage=self.request.get("message")
    message=mail.EmailMessage(sender="sh.sadaf@gmail.com",subject=emailSubject)

    if not mail.is_email_valid(emailAddress):
      self.response.out.write("Email address is not valid.")

    message.to = emailAddress
    message.body="""%s""" %(emailMessage)
    message.send()
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
    ('/Report', Report),
    ('/email', email)
], debug=True)